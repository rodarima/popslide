import numpy as np
import numpy.fft as fft
import alsaaudio as aa
from pykeyboard import PyKeyboard

kbd = PyKeyboard()


CHUNKSIZE = 256
#CHUNKSIZE = 512
RATE = 44100
FREQ_SIZE = CHUNKSIZE//2 + 1
MEM_SIZE = 5

inp = aa.PCM(aa.PCM_CAPTURE)
inp.setchannels(1)
inp.setrate(RATE)
inp.setformat(aa.PCM_FORMAT_S16_LE)
inp.setperiodsize(CHUNKSIZE)

mem = np.zeros(MEM_SIZE)
state = 0
steps = 0

def proc(rec):
	global mem, state, steps

	f = fft.rfft(rec)
	fr = np.abs(f)
	n = rec.size
	timestep = 1/RATE
	freq = np.fft.rfftfreq(n, d=timestep)


	i_freq = np.logical_and(freq > 1900, freq < 3300)
	sel_freq = freq[i_freq]
	sel_fft = fr[i_freq]

	if len(sel_fft) == 0:
		return

	m = np.mean(fr)

	i = np.argmax(sel_fft)
	peak = sel_freq[i]
	peak_max = sel_fft[i]

	max_log = np.log(1 + np.abs(peak_max))

	if max_log < 10.0:
		peak = 0

	#if peak_max < 7.0 * m:
	#	peak = 0

	#print("Peak {} max {}".format(peak, peak_max))
	mem[:-1] = mem[1:]
	mem[-1] = peak

	step_millis = RATE/(CHUNKSIZE*1000)

	if steps > int(300 * step_millis):
		print("TIMEOUT")
		steps = 0
		state = 0
		return

	if peak != 0:
		#print(max_log)
		print(mem)

	if state == 0:
		if np.all(mem[-3:] > 0 ) and np.all(mem[-3:] < 2900):
			print("PRESS")
			#print(mem)
			state = 1
	elif state == 1:
		if peak == 0:
			print("SILENCE")
			state = 2
		steps += 1
	elif state == 2:
		if np.all(mem[-2:] > 2500):
			#print(mem)
			state = 3
			print('RELEASE')
			print('steps = {}'.format(steps))
			if steps < int(50 * step_millis):
				print("NEXT")
				kbd.tap_key(kbd.page_down_key)
			else:
				print("PREV")
				kbd.tap_key(kbd.page_up_key)
			steps = 0
		else:
			steps += 1
	elif state == 3:
		if peak == 0:
			print("SILENCE")
			state = 0

while True:
#for i in range(1000):
	l, data = inp.read()
	rec = np.frombuffer(data, dtype='int16')

	proc(rec)

