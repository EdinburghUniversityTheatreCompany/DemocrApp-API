from abc import ABC


class VoteMethod(ABC):

    @classmethod
    def count(cls, vote_id, **kwargs):
        pass

    @classmethod
    def receive_ballot(cls, vote, voter_token_id, ballot_entries):
        from Meeting.models import BallotEntry
        BallotEntry.objects.filter(token_id=voter_token_id, option__vote=vote).delete()
        cls._handle_ballot(vote, voter_token_id, ballot_entries)

    @classmethod
    def _handle_ballot(cls, vote, voter_token_id, ballot_entries):
        from Meeting.models import BallotEntry
        for ballot_entry in ballot_entries.items():
            value = int(ballot_entry[1])
            option = vote.option_set.filter(pk=ballot_entry[0]).first()
            if option is not None and value >= 1:
                be = BallotEntry(option=option, token_id=voter_token_id, value=value)
                be.save()
