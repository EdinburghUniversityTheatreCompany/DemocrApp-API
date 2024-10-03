import _thread
import logging
from queue import Queue
from threading import Thread
from time import sleep

from openstv.ballots import Ballots
from openstv.MethodPlugins.ScottishSTV import ScottishSTV
from openstv.ReportPlugins.YamlReport import YamlReport
from Meeting.voting_methods.vote_method import VoteMethod

logger = logging.getLogger(__name__)


class STV(VoteMethod):

    @classmethod
    def count(cls, vote_id, **kwargs):
        from Meeting.models import Vote
        vote = Vote.objects.get(pk=vote_id)
        seats = kwargs.get("num_seats", 1)
        assert vote.method == Vote.STV
        _thread.start_new_thread(cls._count, (vote_id, seats))

    @classmethod
    def _count(cls, vote_id, seats):
        from Meeting.models import Vote, BallotEntry, Tie, Option
        vote = Vote.objects.get(pk=vote_id)
        ballots = Ballots()

        options = vote.option_set.all().order_by('pk')
        option_translation = {}
        names = []
        for index, option in enumerate(options):
            option_translation[option.id] = index
            names.append(option.name)
        ballots.setNames(names)
        ballots.numSeats = seats

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
        while countThread.is_alive():
            sleep(0.1)
            if not electionCounter.breakTieRequestQueue.empty():
                [tiedCandidates, names, what] = electionCounter.breakTieRequestQueue.get()
                c = cls.ask_user_to_break_tie(tiedCandidates, names, what, vote)
                electionCounter.breakTieResponseQueue.put(c)
            if "R" in vars(electionCounter):
                status = "Counting votes using {}\nRound: {}".format(electionCounter.longMethodName,
                                                                     electionCounter.R + 1)
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
        vote.results = "Winners: {} \nLosers:{}".format(winners, losers)
        r = YamlReport(electionCounter)
        r.generateReport()
        report = "\n"
        for index, name in enumerate(ballots.names):
            report += "[{}] -> {}\n".format(index, name)

        report += r.outputText
        vote.results += report
        vote.save()

    @classmethod
    def ask_user_to_break_tie(cls, tied_candidates, names, what, vote):
        from Meeting.models import Option, Tie
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
