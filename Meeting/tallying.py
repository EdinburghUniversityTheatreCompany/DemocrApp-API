from threading import Thread
from .models import Vote, BallotEntry, Option
from openstv.ballots import Ballots
from openstv.MethodPlugins.ScottishSTV import ScottishSTV
from time import sleep


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
    for be in BallotEntry.objects.filter(candidate__vote=vote).order_by('token_id', 'value').all():
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
            c = ask_user_to_break_tie(tiedCandidates, names, what, vote)
            electionCounter.breakTieResponseQueue.put(c)
        if "R" in vars(electionCounter):
            status = "Counting votes using %s\nRound: %d" % \
                     (electionCounter.longMethodName, electionCounter.R + 1)
        else:
            status = "Counting votes using %s\nInitializing..." % \
                     electionCounter.longMethodName


def ask_user_to_break_tie(tied_candidates, names, what, vote):
    vote.state = vote.NEEDS_TIE_BREAKER
    vote.save()
    while vote.state == vote.NEEDS_TIE_BREAKER:
        sleep(1)
    # TODO(create a tie model holding tied candidates)
