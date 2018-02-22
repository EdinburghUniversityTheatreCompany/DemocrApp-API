from threading import Thread
from .models import Vote, BallotEntry, Option, Tie
from openstv.ballots import Ballots
from openstv.MethodPlugins.ScottishSTV import ScottishSTV
from time import sleep
import logging
logger = logging.getLogger(__name__)


def yes_no_abs_count(vote_id):
    vote = Vote.objects.get(pk=vote_id)
    assert vote.method == Vote.YES_NO_ABS
    yes_counter = 0
    no_counter = 0
    abs_counter = 0
    actions = {
        vote.option_set.filter(name="yes").first().id: yes_counter,
        vote.option_set.filter(name="no").first().id: no_counter,
        vote.option_set.filter(name="abs").first().id: abs_counter,
    }
    for be in BallotEntry.objects.filter(option__vote=vote, value=1).order_by('token_id', 'value').all():
        if be.option_id in actions.keys():
            actions[be.option_id] += 1
        else:
            logger.error("suspicious ballot entry with id: {} had non y n a option in a y n a vote")
    return yes_counter, no_counter, abs_counter

def run_open_stv(vote_id,seats):
    ballots = Ballots()
    vote = Vote.objects.get(pk=vote_id)

    options = vote.option_set.all().order_by('pk')
    option_translation = {}
    names = []
    for index, option in enumerate(options):
        option_translation[option.id] = index
        names.append(option.name)
    ballots.setNames(names)
    ballots.numSeats = seats  # TODO(Decide on method of storing number of seats available)

    voter = -1
    ballot = []
    for be in BallotEntry.objects.filter(option__vote=vote).order_by('token_id', 'value').all():
        if voter != be.token_id and ballot != []:
            ballots.appendBallot(ballot)
        voter = be.token_id
        ballot.append(option_translation[be.id])

    electionCounter = ScottishSTV(ballots)
    countThread = Thread(target=electionCounter.runElection)
    countThread.start()
    while countThread.isAlive():
        sleep(0.1)
        if not electionCounter.breakTieRequestQueue.empty():
            [tiedCandidates, names, what] = electionCounter.breakTieRequestQueue.get()
            c = ask_user_to_break_tie(tiedCandidates, names, what, vote, names)
            electionCounter.breakTieResponseQueue.put(c)
        if "R" in vars(electionCounter):
            status = "Counting votes using %s\nRound: %d" % \
                     (electionCounter.longMethodName, electionCounter.R + 1)
        else:
            status = "Counting votes using %s\nInitializing..." % \
                     electionCounter.longMethodName
    logger.info(electionCounter.winners)


def ask_user_to_break_tie(tied_candidates, names, what, vote):
    for candidate in names:
        option = Option.objects.filter(name=candidate, vote=vote).first()
        tie = Tie(vote=vote, option=option)
        tie.save()
    vote.state = vote.NEEDS_TIE_BREAKER
    vote.save()
    while vote.state == vote.NEEDS_TIE_BREAKER:
        sleep(1)

    if Tie.objects.filter(vote=vote)[:1].count() > 1:
        logger.error('multiple tie objects after vote')
    tie = Tie.objects.filter(vote=vote).first()
    i = names.index(tie.option.name)
    tie.delete()
    return tied_candidates[i]
