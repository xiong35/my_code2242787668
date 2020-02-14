
import numpy as np
import matplotlib.pyplot as plt
from keras.models import load_model


data_dir = '/root/MySource/jena'

fname = os.path.join(data_dir, 'climate.csv')

f = open(fname)
data = f.read()
f.close()

lines = data.split('\n')
header = lines[0].split(',')
lines = lines[1:]

float_data = np.zeros((len(lines), len(header) - 1))


# the first column of the data is Date
for i, line in enumerate(lines):
    values = [float(x) for x in line.split(',')[1:]]
    float_data[i, :] = values


# standardize the data
# take the first 200000 time steps as training data
mean = float_data[:200000].mean(axis=0)
float_data -= mean
std = float_data[:200000].std(axis=0)
float_data /= std
print('data loaded')

my_model = load_model('/root/MySource/GRU.h5')
print('model loaded')


def generator(data, lookback, delay, min_index, max_index,
              shuffle=False, batch_size=128, step=6):
    if max_index is None:
        max_index = len(data) - delay - 1
    i = min_index + lookback
    while 1:
        if shuffle:
            rows = np.random.randint(
                min_index + lookback, max_index, size=batch_size)
        else:
            if i + batch_size >= max_index:
                i = min_index + lookback
            rows = np.arange(i, min(i + batch_size, max_index))
            i += len(rows)

            # samples = np.zeros((len(rows),          # num of [input for the next procces]
            #                     lookback // step,   # num of previous data
            #                     data.shape[-1]))    # num of features
            # num of [output for the next procces]
        samples = np.zeros((len(rows),
                            lookback // step,
                            data.shape[-1]))
        targets = np.zeros((len(rows),))
        for j, row in enumerate(rows):
            indices = range(rows[j] - lookback, rows[j], step)
            samples[j] = data[indices]
            targets[j] = data[rows[j] + delay][1]
        yield samples, targets


lookback = 1440
step = 6
delay = 144
batch_size = 128

test_gen = generator(float_data,
                     lookback=lookback,
                     delay=delay,
                     min_index=300001,
                     max_index=None,
                     step=step,
                     batch_size=batch_size)

test_steps = (len(float_data) - 300001 - lookback) // batch_size

x_test, y_test = next(test_gen)
print(len(y_test))

predictions = my_model.predict(x_test)

print(len(predictions))

days = range(1, len(predictions)+1)
plt.figure()
plt.plot(days, y_test, 'b', alpha=0.8, label='Real Date')
plt.plot(days, val_loss, 'r', alpha=0.8, label='Predict Date')
plt.title('Real And Predict Curve')
plt.xlabel("days")
plt.ylabel("temp")
plt.legend()
plt.savefig('./images/GRU_predict')
