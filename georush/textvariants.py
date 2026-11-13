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
           '{difficulty} flags, four choices each. You get 3 seconds per question!',
           'Choose A, B, C, or D and beat the 3-second timer. Difficulty: {difficulty}.']
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
            'How did you do? Comment your score ({scores}) and tag a friend who knows flags!',
            # v1.6.4: the video now ends asking for the viewer's country too
            'Score + country! {scores}? And where are you watching from? 🌏',
            'Drop your score ({scores}) and your country below! 🌏',
            'Which country are you from? And your score: {scores}? 👇',
            'Comment your score ({scores}) + your flag! Let’s see who wins 🏆']

SHORT_HASHTAGS = '#GeoRush #GuessTheFlag #FlagQuiz #GeographyQuiz #Shorts'


# v1.4.0 series themes: own titles, intro line, tags and hashtag. {n} is the question count.
REGION_ADJ = {'Africa': 'African', 'Asia': 'Asian', 'Europe': 'European', 'Americas': 'Americas', 'Oceania': 'Oceania'}
REGION_NAME = {'Americas': 'the Americas'}
THEME_TITLES = {
    'region': ['Guess These {n} Flags From {region}! | GeoRush #Shorts',
               '{n} Flags From {region}: Can You Name Them All? | GeoRush #Shorts',
               '{adj} Flag Challenge: Can You Get {n}/{n}? | GeoRush #Shorts'],
    'Lookalike': ['These Flags Look Almost the Same! Can You Tell? | GeoRush #Shorts',
                  'Look-Alike Flags: Can You Get {n}/{n}? | GeoRush #Shorts',
                  'Most People Mix Up These {n} Flags! | GeoRush #Shorts'],
    'Zoom': ['Zoomed-In Flags: Can You Guess Them? | GeoRush #Shorts',
             'Guess the Flag From a Tiny Corner! | GeoRush #Shorts',
             'Zoom Quiz: Name These {n} Flags! | GeoRush #Shorts'],
    'Capital': ['Guess the Capital City! {n} Questions | GeoRush #Shorts',
                'Can You Name These {n} Capitals? | GeoRush #Shorts',
                'Capital City Quiz: Can You Get {n}/{n}? | GeoRush #Shorts'],
    # v1.6.0 Find: challenge-style titles, the style of the channel's best Shorts in Nov 2026.
    'Population': ['Which Country Has the Most People? \U0001F30F | GeoRush #Shorts',
                   'Bigger Population? Most People Get This Wrong! | GeoRush #Shorts',
                   'Guess the Most Populated Country! {n} Rounds | GeoRush #Shorts',
                   'Population Quiz: Can You Get {n}/{n}? | GeoRush #Shorts'],
    'Find': ['Find the Right Flag! Can You Get {n}/{n}? 😈 | GeoRush #Shorts',
             'Can You Find Your Country’s Flag? | GeoRush #Shorts',
             'Pick the Right Flag! Most People Miss One | GeoRush #Shorts',
             'Which Flag Is It? Find {n} Countries Fast! | GeoRush #Shorts'],
}
THEME_INTROS = {
    'region': 'Every flag in this round is from {region}. Can you name all {n} countries?',
    'Lookalike': 'Every flag in this round has a look-alike among the answers. Can you tell all {n} apart?',
    'Capital': 'You see the flag and the country: now name its capital city. {n} questions!',
    'Zoom': 'Every flag starts zoomed in on one small spot. Name the country before the full flag appears!',
    'Population': 'Four flags, one question: which country has the most people? Population data: World Bank (2025), CC BY 4.0.',
    'Find': 'Each round names a country: find its flag among four look-alike flags before the timer runs out!',
}
THEME_TAGS = {'region': ['{region} flags'], 'Lookalike': ['similar flags', 'look alike flags'],
              'Capital': ['capital cities', 'capital city quiz'], 'Zoom': ['zoomed in flags', 'flag zoom quiz'],
              'Find': ['find the flag', 'which flag is it'],
              'Population': ['population quiz', 'most populated countries']}
THEME_HASHTAG = {'region': '#{tag}Flags', 'Lookalike': '#SimilarFlags', 'Capital': '#CapitalCities', 'Zoom': '#FlagZoom', 'Find': '#FindTheFlag', 'Population': '#PopulationQuiz'}
CAPITAL_COMMENTS = ['How many capitals did you get right? {scores}? Tell us your score!',
                    'Which capital tricked you? Share your score ({scores}) below!',
                    'Did you get {count}/{count}? Drop your capital score: {scores}!']


def _themed_short_texts(signature, count, difficulty, theme):
    rng = random.Random(f'{theme}:{signature}')
    key = 'region' if theme in REGION_ADJ else theme
    values = {'n': count, 'region': REGION_NAME.get(theme, theme), 'adj': REGION_ADJ.get(theme, ''), 'tag': theme}
    title = rng.choice(THEME_TITLES[key]).format(**values)
    scores = ', '.join(f'{n}/{count}' for n in range(count+1))
    hashtags = SHORT_HASHTAGS.replace(' #Shorts', ' '+THEME_HASHTAG[key].format(**values)+' #Shorts')
    if key == 'Capital':
        hashtags = hashtags.replace('#GuessTheFlag ', '')
        middle = f'Pick A, B, C or D before the countdown hits zero. Flags: {difficulty}.'
    else:
        middle = rng.choice(MIDDLES).format(difficulty=difficulty)
    description = (THEME_INTROS[key].format(**values)+'\n\n'+middle+'\n'+rng.choice(CALLS)+'\n\n'
                   +rng.choice(FOLLOWS)+'\n\n'+hashtags+'\n')
    tags = ', '.join(CORE_TAGS+[tag.format(**values) for tag in THEME_TAGS[key]]+rng.sample(EXTRA_TAGS, 3)+['Shorts'])
    comment = rng.choice(CAPITAL_COMMENTS if key == 'Capital' else COMMENTS).format(count=count, scores=scores)
    return title, description, tags, comment


def with_episode(title, episode):
    """v1.5.0: 'Flag Challenge #37' style series numbers, so the Shorts read as one running series."""
    if not episode:
        return title
    for brand in (' | GeoRush', ' #Shorts'):
        if brand in title:
            return title.replace(brand, f' #{episode}{brand}', 1)
    return f'{title} #{episode}'


def short_texts(signature, count, difficulty, theme='Classic', episode=None):
    """(title, description, tags, pinned comment) of a Shorts quiz. The draw order is fixed: changing it changes old texts."""
    if theme != 'Classic':
        title, description, tags, comment = _themed_short_texts(signature, count, difficulty, theme)
        return with_episode(title, episode), description, tags, comment
    title, description, tags, comment = _classic_short_texts(signature, count, difficulty)
    return with_episode(title, episode), description, tags, comment


def _classic_short_texts(signature, count, difficulty):
    rng = random.Random(signature)
    titles = [f'Guess These {count} Flags! | GeoRush Geography Quiz #Shorts',
              f'Can You Get {count}/{count}? Flag Challenge | GeoRush #Shorts',
              f'{count} Flags. One Challenge. Can You Win? | GeoRush #Shorts']
    if difficulty == 'Mixed' and count > 1:
        # v1.6.0: challenge-style titles (the channel's top Short is 'Only 1 of These 3 Flags Is Hard').
        # Both claims are true of a Mixed Short: its last flag is the only Hard one.
        titles = [f'Only 1 of These {count} Flags Is Hard 😈 | GeoRush #Shorts',
                  f'Most People Miss the Last Flag! Can You Get {count}/{count}? | GeoRush #Shorts',
                  f'Can You Get {count}/{count}? Flag Challenge | GeoRush #Shorts']
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
LONG_RULES = ['Choose A, B, C or D. Each question has a {cd}-second countdown and a {rv}-second answer reveal.',
              'Pick A, B, C or D before the {cd}-second countdown ends, then see the answer in a {rv}-second reveal.',
              'Every question gives you {cd} seconds to choose A, B, C or D, followed by a {rv}-second answer reveal.']
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


def long_texts(signature, count, countdown=8, reveal=2):
    """(description top part, tags, pinned comment) of a Longform quiz. The chapters and hashtags are added by the caller."""
    rng = random.Random('longform:'+signature)
    top = (rng.choice(LONG_INTROS).format(count=count)+'\n\n'
           +rng.choice(LONG_BODIES)+'\n'
           +rng.choice(LONG_RULES).format(cd=countdown, rv=reveal)+'\n'
           +LONG_DISCLAIMER+'\n\n'
           +rng.choice(LONG_CALLS)+'\n'
           +rng.choice(LONG_FOLLOWS))
    tags = ', '.join(LONG_CORE_TAGS+rng.sample(LONG_EXTRA_TAGS, 4))
    comment = rng.choice(LONG_COMMENTS).format(count=count)
    return top, tags, comment
