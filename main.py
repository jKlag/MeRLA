import midi
from MidiTools import create_chord_progression
from MidiTools import get_notes_per_step
from MidiTools import create_track_from_notes
from Listener_offline import Environment
import csv
import random
import sys

MAX_PATTERN_LENGTH = 128
ACTIONS = range(9)
RES = midi.Pattern().resolution
INIT_NOTE = 0

# if SURVEY is true, will generate three melodies for each chord progression:
# 1. Regular MeRLA melody
# 2. MeRLA melody with no tension reward
# 3. Melody with random policy
SURVEY = False;

# returns the best (greedy with respect to Q) action for given state
# note: if there are multiple "best" actions, will return random choice of best actions
# return format: tuple with (action, value)
def get_best_action(Q,state):
    step = state['step']
    prev_note = state['prev_note']
    best_actions = [("", -sys.maxint)]
    for action in ACTIONS:
        val = Q[step][prev_note][action]
        if val > best_actions[0][1]:
            best_actions = [(action, val)]
        elif val == best_actions[0][1]:
            best_actions.append((action,val))

    # return random choice of best actions
    return random.choice(best_actions)


# main function - runs experiment and writes results to csv
def run_experiment(env, sims, csv_name, num_episodes, gamma):
    # open csv file
    csvfile = open(csv_name,'wb')
    csvwriter = csv.writer(csvfile)

    csvwriter.writerow(['' for i in range(sims+1)])

    results = [[0 for i in range(sims)] for j in range(num_episodes)]

    exp_rate = 0.25
    alpha = 0.1

    for sim in range(sims):
        # randomly initialize action-value function
        Q = [[[] for i in range(9)] for j in range(MAX_PATTERN_LENGTH)]
        for i in range (MAX_PATTERN_LENGTH): # time step
            for j in range(9): # previous action
                Q[i][j] = [random.random() for l in range(9)]

        # append value of making note at end of song (all equal)
        Q.append([[0 for i in range(9)] for j in range(9)])


        for episode in range(num_episodes):
            # reset environment variables
            env.reset()

            # initialize total reward and state
            total_reward = 0.0

            # get initial state from environment
            state = env.get_init_state(INIT_NOTE)

            # iterate through time steps of chord progression (excluding first)
            for step in range(1, len(env.chords)):
                exp_rate = 5.0/(episode+1)
                alpha = 5.0/(episode+1)

                # choose action with e-greedy policy
                r = random.random()
                if r < exp_rate:
                    # choose random action
                    a = random.choice(ACTIONS)
                else:
                    # choose best action
                    a = get_best_action(Q,state)[0]

                prev_note = state['prev_note']

                # get next state from environment based on state, action, and step num
                next_state = env.get_next_state(state, a)

                # get reward from environment
                reward = env.get_reward(state, a)

                # add reward to episode's total reward
                total_reward += reward

                # find the best action (w.r.t. Q) for the next state
                best_action_next_state = get_best_action(Q,next_state)

                # store current q val in tmp variable
                cur_q_val = Q[step][prev_note][a]

                # update q value
                Q[step][prev_note][a] = cur_q_val + (alpha * (reward + (gamma*best_action_next_state[1]) - cur_q_val))

                # update state
                state = next_state

            results[episode][sim] = total_reward

    for episode in results:
        data = episode

        # add on average of all sims
        data.append(sum(episode)/sims)

        # write data row to csv
        csvwriter.writerow(data)

    csvfile.close()

    return Q


def make_melody(env, Q_table = None):
    # reset environment variables
    env.reset()

    # put first MIDI note in MIDI track
    results = [env.note_map[INIT_NOTE] + env.key + 24]

    # get initial state from environment
    state = env.get_init_state(INIT_NOTE)

    # iterate through time steps of chord progression (excluding first and last)
    for step in range(1, len(env.chords)):
        # choose action with greedy policy if Q_table provided
        # otherwise, take random action
        if Q_table == None:
            a = random.choice(ACTIONS)
        else:
            a = get_best_action(Q_table, state)[0]

        # get next state from environment based on state, action, and step num
        next_state = env.get_next_state(state, a)

        # update state
        state = next_state

        # add MIDI note to melody track
        if a == 8:  # rest
            results.append(-1)
        else:
            results.append(env.note_map[a] + env.key + 24)

    return results


####
# MAIN
###

# list of chord progressions to run through MeRLA
chord_progressions = []


chords = [(midi.A_4,'minor', 4, 2),
         (midi.G_4,'major', 4, 2),
         (midi.F_4, 'major', 4, 3),
         (midi.G_4, 'major', 4, 1)]

chord_progressions.append({'chords': chords,
                           'loops': 2,
                           'key': midi.A_4,
                           'scale': 'MIN'})


chords = [(midi.C_4,'major', 2, 2),
         (midi.A_4,'minor', 2, 2),
         (midi.C_4, 'major', 2, 2),
         (midi.A_4, 'minor', 2, 2),
         (midi.F_4, 'major', 2, 2),
         (midi.G_4, 'major', 2, 2),
         (midi.C_4, 'major', 2, 2),
         (midi.G_4, 'major', 2, 2)]

chord_progressions.append({'chords': chords,
                           'loops': 2,
                           'key': midi.C_4,
                           'scale': 'MAJ'})

chords = [(midi.C_4,'major', 2, 4),
         (midi.A_4,'minor', 2, 4),
         (midi.D_4, 'minor', 2, 4),
         (midi.G_4, 'major', 2, 4)]

chord_progressions.append({'chords': chords,
                           'loops': 2,
                           'key': midi.C_4,
                           'scale': 'MAJ'})


for i in range(len(chord_progressions)):
    # Instantiate a MIDI Pattern (contains a list of tracks)
    pattern = midi.Pattern()

    chords = chord_progressions[i]['chords']
    key = chord_progressions[i]['key']
    scale = chord_progressions[i]['scale']
    loops = chord_progressions[i]['loops']

    # make track with verse chord progression
    chords_track = create_chord_progression(chords, loops, RES)

    # Append track with backing chords to the pattern
    pattern.append(chords_track)

    chord_steps = get_notes_per_step(chords_track, RES)

    # create Environment from chords, key, and scale type
    env = Environment(chord_steps, key, scale)

    # get action-value tables through q-learning
    action_value = run_experiment(env, 5, 'results_chord_prog%d.csv'%i, 2000, 0.9)

    # create melody tracks using learned action-value tables
    melody_steps = make_melody(env, action_value)

    melody = create_track_from_notes(melody_steps, RES)

    # Append the melody and random melody tracks to the pattern
    pattern.append(melody)

    # Add the end of track event, append it to all tracks
    eot = midi.EndOfTrackEvent(tick=1)
    chords_track.append(eot)
    melody.append(eot)

    if SURVEY:
        # create seperate environment with no tension reinforcement and generate melody
        env_no_tension = Environment(chord_steps, key, scale)
        env_no_tension.set_weights(2, 0.5, 0, 1, 0.5)
        action_value_no_tension = run_experiment(env, 1, 'results_chord_prog%d_no_tension_2.csv' % i, 2000, 0.9)
        melody_steps_no_tension = make_melody(env_no_tension, action_value_no_tension)
        melody_no_tension = create_track_from_notes(melody_steps_no_tension, RES)

        # create random melody track for comparison
        random_melody = create_track_from_notes(make_melody(env), RES)

        pattern.append(melody_no_tension)
        pattern.append(random_melody)

        melody_no_tension.append(eot)
        random_melody.append(eot)

    # Save the pattern to disk
    midi.write_midifile("chord_prog%d_2.mid"%i, pattern)
