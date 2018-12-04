import midi

# the amount of tension built when each note played
TENSION = [1, 1.2, 1, 1.4, 1, 1.1, 1.6, 1, 1]

INTERVAL_VALS = [0, 1, 0.5, -1, 1, -1, -1, -1]

CHORD_FITS = [1, -1, 1, -2, 1, -1, -2]

class Environment:
    chords = []
    note_map = []

    weights = {
        'chord_fit': 2,
        'restlessness': 0.5,
        'tension': 1,
        'interval': 1,
        'clutter' : 0.5
    }

    key = midi.C_4
    scale = 'MAJ'

    last_played = 0
    tension = 0
    restlessness = 0
    clutter = 0

    def __init__(self, chords, key, scale):
        self.key = key
        self.scale = scale

        if scale == 'MAJ':
            self.note_map = [0, 2, 4, 5, 7, 9, 11, 12]
        elif scale == 'MIN':
            self.note_map = [0, 2, 3, 5, 7, 8, 10, 12]

        self.chords = self.make_key_relative(chords)

    def make_key_relative(self, chords):
        result = []
        for chord in chords:
            notes = []
            for note in chord:
                notes.append(self.note_map.index((note-self.key)%12))
            result.append(notes)

        return result

    def set_weights(self, chord_fit, restlessness, tension, interval, clutter):
        self.weights['chord_fit'] = chord_fit
        self.weights['restlessness'] = restlessness
        self.weights['tension'] = tension
        self.weights['interval'] = interval
        self.weights['clutter'] = clutter


    def reset(self):
        self.tension = 0
        self.restlessness = 0
        self.clutter = 0

    def get_init_state(self, init_note):
        first_state = {'step': 1,
                     'prev_note': init_note}

        return first_state

    def get_next_state(self, state, action):
        # extract values from state
        step = state['step']

        # construct new state
        new_state = {'step': step + 1,
                     'prev_note': action}

        return new_state


    def get_reward(self, state, action):
        reward = 0

        # extract values from new state
        step = state['step']
        chord = self.chords[step]
        chord_root = chord[0]
        prev_note = state['prev_note']
        note = action

        # if silence, add tension
        if note == 8:
            # reset clutter
            self.clutter = 0
            # add multiple of current tension
            self.tension += TENSION[8]*self.tension
            if prev_note == 6:
                reward -= self.weights['interval']
        else:
            # if previous note was a rest, look at last played
            if prev_note == 8:
                prev_note = self.last_played
            else:
                # apply clutter punishment and update clutter
                reward -= self.weights['clutter']
                self.clutter += 1

            # apply interval reinforcement
            note_interval = abs(note - prev_note)
            reward += self.weights['interval'] * INTERVAL_VALS[note_interval]

            # apply chord fit reinforcement
            chord_interval = (note - chord_root)%7
            reward += self.weights['chord_fit'] * CHORD_FITS[chord_interval]

            # apply tension reward (release) or add (build) tension
            if (note == 0 or note == 7) and chord_root == 0:
                if prev_note == 8:
                    reward += TENSION[8] * self.weights['tension'] * self.tension
                else:
                    reward += self.weights['tension'] * self.tension
                self.tension = 0
            elif note == 4 and (chord_root == 0 or chord_root == 4):
                reward += self.tension / 2
                self.tension = self.tension / 2
            else:
                self.tension *= TENSION[note]

            self.last_played = note

        # update restlessness and apply restlessness punishment
        if note == prev_note:
            self.restlessness += 1
        else:
            self.restlessness = 0
        reward -= self.restlessness * self.weights['restlessness']

        return reward
