from .models import Vote, BallotEntry, Option
from openstv.ballots import Ballots

def runOpenSTV(vote_id):
    ballots = Ballots()
    vote = Vote.objects.get(pk=vote_id)
    options = vote.option_set.all().order_by('pk')
    option_translation = {}
    names = []
    for index, option in enumerate(options):
        option_translation[option.id] = index
        names.append(option.name)
    ballots.setNames(names)
    voter = -1
    ballot = []
    for be in BallotEntry.objects.filter(candidate__vote=vote).order_by('token_id', 'value').all():
        if voter != be.token_id and ballot != []:
            ballots.appendBallot(ballot)
        voter = be.token_id
        ballot.append(option_translation[be.id])



