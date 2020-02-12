
from keras.optimizers import RMSprop
from keras import layers
from keras.models import Sequential
import numpy as np
import os
import matplotlib.pyplot as plt

data_dir = '/root/MySource/jena'  # TODO

fname = os.path.join(data_dir, 'climate.csv')

f = open(fname)
data = f.read()
f.close()

lines = data.split('\n')
header = lines[0].split(',')
lines = lines[1:]

float_data = np.zeros((len(lines), len(header)-1))


# the first column of the data is Date
for i, line in enumerate(lines):
    values = [float(x) for x in line.split(',')[1:]]
    float_data[i, :] = values

# the new first column is temp(erature)
temp = float_data[:, 1]
plt.plot(range(1440), temp[:1440])
plt.show()

# standardize the data
# take the first 200000 time steps as training data
mean = float_data[:200000].mean(axis=0)
float_data -= mean
std = float_data[:200000].std(axis=0)
float_data /= std


# def a generator that returns a tuple (samples, targets)
# samples for a batch of input
# targets for a list of temperatures
def generator(
    data,           # standardized data
    lookback,       # how many previous time steps should consider
                    # in the next procces
    delay,          # how many time steps between now and target
    min_index,      # define to choose which steps
    max_index,
    shuffle=False,  # whether to shuffle the data
    batch_size=128,
    step=6          # the interval step between two samples
):
    if max_index is None:
        max_index = len(data) - delay - 1
    i = min_index + lookback
    while True:
        if shuffle:
            rows = np.random.randint(
                min_index+lookback, max_index, size=batch_size)
        else:
            if i + batch_size >= max_index:
                i = min_index + lookback
            rows = np.arange(i, min(i+batch_size, max_index))
            i += len(rows)

        samples = np.zeros((len(rows),          # num of [input for the next procces]
                            lookback // step,   # num of previous data
                            data.shape[-1]))    # num of features
        # num of [output for the next procces]
        targets = np.zeros((len(rows),))
        for j, row in enumerate(rows):
            # indice mean which steps should be drawn for the next procces
            indices = range(rows[j]-lookback, rows[j], step)
            # mat[(range)] means to choose the rows in the range
            samples[j] = data[indices]
            targets[j] = data[rows[j]+delay][1]
        yield samples, targets


lookback = 1440
step = 6
delay = 144
batch_size = 128

train_gen = generator(float_data, lookback=lookback,
                      delay=delay, min_index=0,
                      max_index=200000, shuffle=True,
                      step=step, batch_size=batch_size)

val_gen = generator(float_data, lookback=lookback,
                    delay=delay, min_index=200001,
                    max_index=300000, step=step,
                    batch_size=batch_size)

test_gen = generator(float_data, lookback=lookback,
                     delay=delay, min_index=300001,
                     max_index=None, step=step,
                     batch_size=batch_size)

# to see the whole dataset, how many times to sample from val_gen
val_steps = (300000 - 200001 - lookback)//batch_size
test_gen = (len(float_data)-300001 - lookback)//batch_size


##### train a GRU with dropout #####

model = Sequential()
model.add(layers.GRU(32, dropout=0.2, recurrent_dropout=0.2,
                     input_shape=(None, float_data.shape[-1])))

model.add(layers.Dense(1))

model.compile(optimizer=RMSprop(), loss='mse')
history = model.fit_generator(train_gen, steps_per_epoch=5,# 500
                              epochs=3, validation_data=val_gen, # epochs=40
                              validation_steps=val_steps)

loss = history.history['loss']
val_loss = history.history['val_loss']

epochs = range(1, len(loss)+1)

plt.figure()

plt.plot(epochs, loss, 'bo', label='Training loss')
plt.plot(epochs, val_loss, 'b', label='Validation loss')
plt.title('Training and validation loss')
plt.legend()
plt.savefig('./images/GRU_mpl2')
