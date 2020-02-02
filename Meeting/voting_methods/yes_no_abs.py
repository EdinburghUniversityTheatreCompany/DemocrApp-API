import logging

from Meeting.voting_methods.vote_method import VoteMethod

logger = logging.getLogger(__name__)


class YNA(VoteMethod):

    @classmethod
    def count(cls, vote, **kwargs):
        from Meeting.models import Vote, BallotEntry
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
        y, n, a = counts.values()
        vote.results = "Y:{},N:{},A{}".format(y, n, a)
        vote.save()
