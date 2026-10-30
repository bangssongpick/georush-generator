"""Per-video wording for the upload text (description, tags, pinned comment). Plain data, no heavy imports.

The wording is chosen from the quiz signature, so one quiz always gets the same text while different quizzes differ.
Every variant keeps the branding hashtags, the @GeoRushGames mention and the score ask; none names a country.
"""
import random

# ---- Shorts -------------------------------------------------------------------------------------------------
INTROS = ['Can you guess all {count} countries from their flags?',
          'Think you know your flags? Try to name all {count} countries!',
          'How many of these {count} flags can you name?',
          'Ready for a quick flag challenge? Guess all {count} countries!',
          'Can you name every country from its flag? {count} flags, one try each.']
MIDDLES = ['{difficulty} flag challenge: choose A, B, C, or D before the timer runs out.',
           'Pick A, B, C or D before the countdown hits zero. This round: {difficulty} flags.',
           '{difficulty} flags, four choices each. You get 5 seconds per question!',
           'Choose A, B, C, or D and beat the 5-second timer. Difficulty: {difficulty}.']
CALLS = ['Test your geography knowledge and share your score in the comments!',
         'Comment your score and challenge a friend to beat it!',
         'Tell us your score in the comments: which flag was the hardest?',
         'Share your score below and see how you compare with other viewers!']
FOLLOWS = ['Subscribe to GeoRush (@GeoRushGames) for more flag challenges.',
           'Follow GeoRush (@GeoRushGames) for more flag quizzes.',
           'More flags are coming: subscribe to GeoRush (@GeoRushGames)!',
           'Subscribe to GeoRush (@GeoRushGames) and keep guessing flags.']
CORE_TAGS = ['GeoRush', 'GeoRushGames', 'guess the flag', 'flag quiz', 'geography quiz']
EXTRA_TAGS = ['country flags', 'geography challenge', 'world flags', 'flags of the world', 'guess the country',
              'flag game', 'geography trivia', 'general knowledge', 'quiz game', 'flag challenge']
COMMENTS = ['How many flags did you get right? {scores}? Tell us your score!',
            'What was your score? {scores}? Drop it in the comments!',
            'Did you get {count}/{count}? Tell us your score: {scores}!',
            'Score check! {scores}: comment yours and challenge a friend!',
            'Which flag tricked you? Share your score ({scores}) below!',
            'Think you can beat {count}/{count}? Drop your score ({scores}) in the comments!',
            'Be honest: what was your score? {scores}?',
            'How did you do? Comment your score ({scores}) and tag a friend who knows flags!']

SHORT_HASHTAGS = '#GeoRush #GuessTheFlag #FlagQuiz #GeographyQuiz #Shorts'


def short_texts(signature, count, difficulty):
    """(title, description, tags, pinned comment) of a Shorts quiz. The draw order is fixed: changing it changes old texts."""
    rng = random.Random(signature)
    titles = [f'Guess These {count} Flags! | GeoRush Geography Quiz #Shorts',
              f'Can You Get {count}/{count}? Flag Challenge | GeoRush #Shorts',
              f'{count} Flags. One Challenge. Can You Win? | GeoRush #Shorts']
    scores = ', '.join(f'{n}/{count}' for n in range(count+1))
    title = rng.choice(titles)
    description = (rng.choice(INTROS).format(count=count)+'\n\n'
                   +rng.choice(MIDDLES).format(difficulty=difficulty)+'\n'
                   +rng.choice(CALLS)+'\n\n'
                   +rng.choice(FOLLOWS)+'\n\n'
                   +SHORT_HASHTAGS+'\n')
    tags = ', '.join(CORE_TAGS+rng.sample(EXTRA_TAGS, 4)+['Shorts'])
    comment = rng.choice(COMMENTS).format(count=count, scores=scores)
    return title, description, tags, comment


# ---- Longform -----------------------------------------------------------------------------------------------
LONG_INTROS = ['Can you identify all {count} country flags?',
               'Think you can name all {count} country flags?',
               'How many of these {count} country flags can you name?',
               'Ready for a big flag challenge? Name all {count} countries!',
               '{count} flags, four levels. Can you name them all?']
LONG_BODIES = ['Test your geography knowledge in this Easy to Expert challenge!',
               'Start with easy flags and work your way up to the experts!',
               'From well-known flags to real head-scratchers: how far can you get?',
               'Find out whether you are a flag rookie or a geography pro!']
LONG_RULES = ['Choose A, B, C or D. Each question has an 8-second countdown and a 2-second answer reveal.',
              'Pick A, B, C or D before the 8-second countdown ends, then see the answer in a 2-second reveal.',
              'Every question gives you 8 seconds to choose A, B, C or D, followed by a 2-second answer reveal.']
LONG_DISCLAIMER = 'Difficulty tiers are editorial groupings, not measured player ratings. Familiarity varies by viewer.'
LONG_CALLS = ['Watch until the end and share your final score.',
              'Stay until the end and tell us your final score in the comments!',
              'Keep score as you play and share your result at the end.']
LONG_FOLLOWS = ['Subscribe to GeoRush (@GeoRushGames) for more geography challenges.',
                'Follow GeoRush (@GeoRushGames) for more geography quizzes.',
                'More flag challenges are coming: subscribe to GeoRush (@GeoRushGames)!',
                'Subscribe to GeoRush (@GeoRushGames) and keep testing your geography.']
LONG_CORE_TAGS = ['GeoRush', 'guess the flag', 'flag quiz', 'geography quiz']
LONG_EXTRA_TAGS = ['world flags', 'guess the country', 'geography challenge', 'flags of the world', 'country flags',
                   'geography trivia', 'long quiz', 'flag game', 'general knowledge', 'quiz game']
LONG_COMMENTS = ['How many flags did you recognize? Share your score out of {count}!',
                 'What was your final score out of {count}? Tell us below!',
                 'Be honest: how many of the {count} flags did you get? Drop your score!',
                 'Which round was the hardest? Share your score out of {count} in the comments!',
                 'Think you can get {count}/{count}? Comment your score and challenge a friend!']
LONG_HASHTAGS = '#GeoRush #FlagQuiz #GeographyQuiz #GuessTheFlag'


def long_texts(signature, count):
    """(description top part, tags, pinned comment) of a Longform quiz. The chapters and hashtags are added by the caller."""
    rng = random.Random('longform:'+signature)
    top = (rng.choice(LONG_INTROS).format(count=count)+'\n\n'
           +rng.choice(LONG_BODIES)+'\n'
           +rng.choice(LONG_RULES)+'\n'
           +LONG_DISCLAIMER+'\n\n'
           +rng.choice(LONG_CALLS)+'\n'
           +rng.choice(LONG_FOLLOWS))
    tags = ', '.join(LONG_CORE_TAGS+rng.sample(LONG_EXTRA_TAGS, 4))
    comment = rng.choice(LONG_COMMENTS).format(count=count)
    return top, tags, comment
