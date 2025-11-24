import numpy as np
import matplotlib.pyplot as plt

# Exercise 3

N = 1024
t0 = 0.5
sigma2 = 1 / 500
sigma = np.sqrt(sigma2)
t_n = np.arange(N) / N  
s_n = np.exp(-((t_n - t0) ** 2) / sigma2)  

s_fft = np.fft.fft(s_n) / N 
frequencies = np.fft.fftfreq(N)  
s_fft_modulus = np.abs(s_fft)  

plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(t_n, s_n, label='Signal $s_n$')
plt.title('Discrete Signal $s_n$')
plt.xlabel('Time $t_n$')
plt.ylabel('$s_n$')
plt.grid(True)
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(frequencies, s_fft_modulus, label='Spectrum $|\\tilde{s}_k|$', color='orange')
plt.title('Spectrum $|\\tilde{s}_k|$')
plt.xlabel('Frequency')
plt.ylabel('Magnitude')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()

# Exercise 4

f0 = 64
m_values = np.arange(0, N // f0)  
positions = m_values * (N // f0)  

d_n = np.zeros(N)
d_n[positions] = 1

d_fft = np.fft.fft(d_n) / N
d_fft_modulus = np.abs(d_fft) 

frequencies = np.fft.fftfreq(N)  

plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.stem(np.arange(N), d_n, use_line_collection=True, basefmt=" ", label='Dirac Pulse $d_n$')
plt.title('Discrete Dirac Pulse $d_n$')
plt.xlabel('Index $n$')
plt.ylabel('$d_n$')
plt.grid(True)
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(frequencies, d_fft_modulus, color='orange', label='Spectrum $|\\tilde{d}_k|$')
plt.title('Spectrum $|\\tilde{d}_k|$')
plt.xlabel('Frequency')
plt.ylabel('Magnitude')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()

# Exercise 5

r_n = s_n * d_n

r_fft = np.fft.fft(r_n) / N
r_fft_modulus = np.abs(r_fft)

plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.stem(np.arange(N), r_n, use_line_collection=True, basefmt=" ", label='Sampled Signal $r_n$')
plt.title('Sampled Signal $r_n$')
plt.xlabel('Index $n$')
plt.ylabel('$r_n$')
plt.grid(True)
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(frequencies, r_fft_modulus, color='orange', label='Spectrum $|\\tilde{r}_k|$')
plt.title('Spectrum of Sampled Signal $|\\tilde{r}_k|$')
plt.xlabel('Frequency')
plt.ylabel('Magnitude')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()

# Exercise 6

kc = f0 // 2 

r_fft_filtered = np.zeros_like(r_fft)
r_fft_filtered[:kc] = r_fft[:kc] 
r_fft_filtered[-kc:] = r_fft[-kc:]  

s_rec = np.fft.ifft(r_fft_filtered) * N  

plt.figure(figsize=(10, 5))
plt.plot(t_n, np.real(s_rec), label='Reconstructed Signal $s_{\\mathrm{rec}}$', color='green')
plt.title('Reconstructed Signal $s_{\\mathrm{rec}}$')
plt.xlabel('Time $t_n$')
plt.ylabel('$s_{\\mathrm{rec}}$')
plt.grid(True)
plt.legend()
plt.show()

# Exercise 7

f0_values = [32, 64, 128]

fig, axs = plt.subplots(len(f0_values), 3, figsize=(15, 10))
fig.suptitle("Effect of Different $f_0$ on Sampling and Reconstruction", fontsize=16)
kc_values = [f // 2 for f in f0_values]

for i, f0 in enumerate(f0_values):
    kc = kc_values[i]
 
    m_values = np.arange(0, N // f0)
    positions = m_values * (N // f0)
    d_n = np.zeros(N)
    d_n[positions] = 1
    
    r_n = s_n * d_n
    
    r_fft = np.fft.fft(r_n) / N

    r_fft_filtered = np.zeros_like(r_fft)
    r_fft_filtered[:kc] = r_fft[:kc]
    r_fft_filtered[-kc:] = r_fft[-kc:]
    
    s_rec = np.fft.ifft(r_fft_filtered) * N

    axs[i, 0].stem(np.arange(N), r_n, use_line_collection=True, basefmt=" ", label=f"Sampled Signal ($f_0 = {f0}$)")
    axs[i, 0].set_title(f"Sampled Signal ($f_0 = {f0}$)")
    axs[i, 0].set_xlabel("Index $n$")
    axs[i, 0].set_ylabel("$r_n$")
    axs[i, 0].grid(True)
    axs[i, 0].legend()

    axs[i, 1].plot(np.fft.fftfreq(N), np.abs(r_fft), label="Original Spectrum", color="orange")
    axs[i, 1].plot(np.fft.fftfreq(N), np.abs(r_fft_filtered), label="Filtered Spectrum", color="blue")
    axs[i, 1].set_title("Spectrum")
    axs[i, 1].set_xlabel("Frequency")
    axs[i, 1].set_ylabel("Magnitude")
    axs[i, 1].grid(True)
    axs[i, 1].legend()

    axs[i, 2].plot(t_n, np.real(s_rec), label=f"Reconstructed Signal ($f_0 = {f0}$)", color="green")
    axs[i, 2].set_title("Reconstructed Signal")
    axs[i, 2].set_xlabel("Time $t_n$")
    axs[i, 2].set_ylabel("$s_{rec}$")
    axs[i, 2].grid(True)
    axs[i, 2].legend()

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()

#Exercise 8

import librosa
import soundfile as sf

file_path = 'Cicadas_in_Greece.ogg'  
signal, fs = librosa.load(file_path, sr=None)  

duration = len(signal) / fs

t = np.linspace(0, duration, len(signal), endpoint=False)

fft_signal = np.fft.fft(signal)
frequencies = np.fft.fftfreq(len(signal), d=1/fs)  

plt.figure(figsize=(14, 6))

plt.subplot(1, 2, 1)
plt.plot(t, signal, label="Audio Signal")
plt.title("Audio Signal (Time Domain)")
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.grid(True)
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(frequencies[:len(signal) // 2], np.abs(fft_signal[:len(signal) // 2]) / len(signal), label="Spectrum")
plt.title("Spectrum (Frequency Domain)")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()

f_low = 2000
f_high = 5000

filtered_fft_signal = np.copy(fft_signal)
filtered_fft_signal[np.abs(frequencies) < f_low] = 0  
filtered_fft_signal[np.abs(frequencies) > f_high] = 0  

reconstructed_signal = np.fft.ifft(filtered_fft_signal).real

min_val = min(signal.min(), reconstructed_signal.min())
max_val = max(signal.max(), reconstructed_signal.max())

time = np.linspace(0, len(signal) / fs, len(signal), endpoint=False)

plt.figure(figsize=(14, 8))

plt.subplot(2, 1, 1)
plt.plot(time, signal, label='Original Signal')
plt.title('Original Signal')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.grid(True)
plt.legend()
plt.ylim(min_val, max_val)  

plt.subplot(2, 1, 2)
plt.plot(time, reconstructed_signal, label='Reconstructed Signal (2000-5000 Hz)', color='orange')
plt.title('Reconstructed Signal')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.grid(True)
plt.legend()
plt.ylim(min_val, max_val)  

plt.tight_layout()
plt.show()

output_path = 'reconstructed_signal.wav'
sf.write(output_path, reconstructed_signal, fs)

print(f"Signal reconstruit sauvegardé dans '{output_path}'")