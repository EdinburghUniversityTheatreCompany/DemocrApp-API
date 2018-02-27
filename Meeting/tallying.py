from queue import Queue
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
    counts = {
        vote.option_set.filter(name="yes").first().id: 0,
        vote.option_set.filter(name="no").first().id: 0,
        vote.option_set.filter(name="abs").first().id: 0,
    }
    for be in BallotEntry.objects.filter(option__vote=vote, value=1).order_by('token_id', 'value').all():
        if be.option_id in counts.keys():
            counts[be.option_id] += 1
        else:
            logger.error("suspicious ballot entry with id: {} had non y n a option in a y n a vote")
    return counts.values()


def run_open_stv(vote_id, seats):
    ballots = Ballots()
    vote = Vote.objects.get(pk=vote_id)

    options = vote.option_set.all().order_by('pk')
    option_translation = {}
    names = []
    for index, option in enumerate(options):
        option_translation[option.id] = index
        names.append(option.name)
    ballots.setNames(names)
    ballots.numSeats = int(seats)  # TODO(Decide on method of storing number of seats available)

    voter = -1
    ballot = []
    for be in BallotEntry.objects.filter(option__vote=vote).order_by('token_id', 'value').all():
        if voter != be.token_id and ballot != []:
            ballots.appendBallot(ballot)
            ballot = []
        voter = be.token_id
        ballot.append(option_translation[be.option_id])
    if ballots != []:
        ballots.appendBallot(ballot)

    electionCounter = ScottishSTV(ballots)
    electionCounter.strongTieBreakMethod = "manual"
    electionCounter.breakTieRequestQueue = Queue(1)
    electionCounter.breakTieResponseQueue = Queue(1)
    countThread = Thread(target=electionCounter.runElection)
    countThread.start()
    while countThread.isAlive():
        sleep(0.1)
        if not electionCounter.breakTieRequestQueue.empty():
            [tiedCandidates, names, what] = electionCounter.breakTieRequestQueue.get()
            c = ask_user_to_break_tie(tiedCandidates, names, what, vote)
            electionCounter.breakTieResponseQueue.put(c)
        if "R" in vars(electionCounter):
            status = "Counting votes using {}\nRound: {}".format(electionCounter.longMethodName, electionCounter.R + 1)
        else:
            status = "Counting votes using %s\nInitializing..." % \
                     electionCounter.longMethodName
        logger.debug(status)
    logger.info(electionCounter.winners)
    vote.refresh_from_db()
    vote.state = Vote.CLOSED
    winners = []
    losers = []
    for w in electionCounter.winners:
        winners.append(ballots.names[w])
    for l in electionCounter.losers:
        losers.append(ballots.names[l])
    vote.description = "Winners: {} \nLosers:{}".format(winners, losers)
    vote.save()


def ask_user_to_break_tie(tied_candidates, names, what, vote):
    for candidate in names:
        option = Option.objects.filter(name=candidate, vote=vote).first()
        tie = Tie(vote=vote, option=option)
        tie.save()
    vote.state = vote.NEEDS_TIE_BREAKER
    vote.save()
    while vote.state == vote.NEEDS_TIE_BREAKER:
        sleep(1)
        vote.refresh_from_db()

    if Tie.objects.filter(vote=vote)[:1].count() > 1:
        logger.error('multiple tie objects after vote')
    tie = Tie.objects.filter(vote=vote).first()
    i = names.index(tie.option.name)
    tie.delete()
    return tied_candidates[i]
