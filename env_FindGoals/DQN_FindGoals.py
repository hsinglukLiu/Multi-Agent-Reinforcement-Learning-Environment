# just click run and see
from env_FindGoals import EnvFindGoals
from keras.models import Sequential
from matplotlib.gridspec import GridSpec
from keras.layers.core import Dense, Flatten, Activation
from keras.layers.convolutional import Conv2D
from keras.optimizers import Adam
import numpy as np
import matplotlib.pyplot as plt
import random


def print_action_freq(a_list):
    temp_data_len = len(a_list)
    freq = np.zeros((1, 5))
    for k in range(temp_data_len):
        freq[0, int(a_list[k])] = freq[0, int(a_list[k])] + 1
    print(freq)

max_opt_iter = 100
max_MC_iter = 100
global_loss = []
global_best = -100000
action_num = 5

env = EnvFindGoals()

model_1 = Sequential()
model_1.add(Conv2D(16, kernel_size=3, data_format="channels_last", input_shape=(3, 3, 3), strides=(1, 1), padding="same"))
model_1.add(Activation('relu'))
model_1.add(Flatten())
model_1.add(Dense(units=50, activation='relu'))
model_1.add(Dense(units=action_num, activation='linear'))
adam = Adam(lr=1e-4)
model_1.compile(loss='mse', optimizer=adam)

model_2 = Sequential()
model_2.add(Conv2D(16, kernel_size=3, data_format="channels_last", input_shape=(3, 3, 3), strides=(1, 1), padding="same"))
model_2.add(Activation('relu'))
model_2.add(Flatten())
model_2.add(Dense(units=50, activation='relu'))
model_2.add(Dense(units=action_num, activation='linear'))
adam = Adam(lr=1e-4)
model_2.compile(loss='mse', optimizer=adam)




annealing = 0.5
for opt_iter in range(max_opt_iter):
    print("iteration ", opt_iter)

    # generate an episode
    env.reset()
    batch_1 = [[], [], [], []]  # obs, q, a, r_1, r_2
    batch_2 = [[], [], [], []]
    done = 0
    annealing = annealing * 0.99
    print("annealing", annealing)
    for MC_iter in range(max_MC_iter):

        obs_1 = env.get_agt1_obs()
        obs_2 = env.get_agt2_obs()
        batch_1[0].append(obs_1)
        batch_2[0].append(obs_2)

        # predict Q value for each action
        obs_1 = obs_1.reshape((1, 3, 3, 3))
        obs_2 = obs_1.reshape((1, 3, 3, 3))
        q_1 = model_1.predict(obs_1)
        q_2 = model_2.predict(obs_2)
        batch_1[1].append(q_1)
        batch_2[1].append(q_2)

        # choose action with maximal Q value
        if random.random() < annealing:
            a_1 = random.randint(0, action_num - 1)
        else:
            a_1 = np.argmax(q_1)

        if random.random() < annealing:
            a_2 = random.randint(0, action_num - 1)
        else:
            a_2 = np.argmax(q_2)


        batch_1[2].append(a_1)
        batch_2[2].append(a_2)

        # excute action
        reward_1, reward_2, obs_1, obs_2 = env.step(a_1, a_2)
        batch_1[3].append(reward_1)
        batch_2[3].append(reward_2)


        if done == 1:   # sample 1 more time
            break

        if reward_1 > 0 or reward_2 > 0:
            done = 1

    # form target
    datalen = len(batch_1[0])
    print("episode length= ", datalen)

    target_1 = np.array(batch_1[1]).reshape((datalen, action_num))
    for i in range(datalen - 2, -1, -1):
        target_1[i][int(batch_1[2][i])] = batch_1[3][i] + 0.99 * np.max(batch_1[1][i + 1])

    target_2 = np.array(batch_2[1]).reshape((datalen, action_num))
    for i in range(datalen-1):
        target_2[i][int(batch_2[2][i])] = batch_2[3][i] + 0.99 * np.max(batch_2[1][i + 1])

    train_x_1 = np.array(batch_1[0]).reshape((datalen, 3, 3, 3))
    train_x_2 = np.array(batch_2[0]).reshape((datalen, 3, 3, 3))
    train_y_1 = target_1
    train_y_2 = target_2

    # train neural network
    model_1.fit(train_x_1, train_y_1, batch_size=32, epochs=10, verbose=0, shuffle=True)
    model_2.fit(train_x_2, train_y_2, batch_size=32, epochs=10, verbose=0, shuffle=True)

    acc_reward = np.sum(batch_1[3]) / datalen


    print("Accumulated Reward", acc_reward)

    if acc_reward > global_best:
        global_best = acc_reward
        # model_1.save_weights('DQN_FindGoals_model1.h5')
        # model_2.save_weights('DQN_FindGoals_model2.h5')
        print("save new model")

    global_loss.append(acc_reward)
    print_action_freq(batch_1[2])
    print_action_freq(batch_2[2])
    print(" ")

x = np.arange(0, max_opt_iter)
fig = plt.figure()
gs = GridSpec(2, 2, figure=fig)
ax1 = fig.add_subplot(gs[0:1, 0:2])
ax2 = fig.add_subplot(gs[1:2, 0:1])
ax3 = fig.add_subplot(gs[1:2, 1:2])
env.reset()
for MC_iter in range(max_MC_iter):
    print(MC_iter)
    ax1.imshow(env.get_full_obs())
    ax2.imshow(env.get_agt1_obs())
    ax3.imshow(env.get_agt2_obs())
    obs_1 = env.get_agt1_obs()
    obs_2 = env.get_agt2_obs()
    obs_1 = obs_1.reshape((1, 3, 3, 3))
    obs_2 = obs_1.reshape((1, 3, 3, 3))
    q_1 = model_1.predict(obs_1)
    q_2 = model_2.predict(obs_2)
    a_1 = np.argmax(q_1)
    a_2 = np.argmax(q_2)
    reward_1, reward_2, obs_1, obs_2 = env.step(a_1, a_2)
    plt.pause(.5)
    plt.draw()