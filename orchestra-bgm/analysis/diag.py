import numpy as np, soundfile as sf, json, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
import orchestra as O
SR=44100
BANDS=[(30,150),(150,400),(400,1000),(1000,2500),(2500,6000),(6000,16000)]
def benv(x,hop=220):
    out=[]
    for a,b in BANDS:
        y=sosfiltfilt(butter(4,[a,min(b,SR/2-100)],'band',fs=SR,output='sos'),x)
        n=len(y)//hop; out.append(10*np.log10(np.mean(y[:n*hop].reshape(n,hop)**2,1)+1e-14))
    return np.array(out)
def onset(x):
    e=np.abs(x); i=np.argmax(e>0.1*e.max()); return max(0,i-200)
def plot(name, real, syn, path, T=2.0):
    real=real[onset(real):][:int(T*SR)]; syn=syn[onset(syn):][:int(T*SR)]
    syn=syn/np.sqrt(np.mean(syn**2))*np.sqrt(np.mean(real**2))
    R,S=benv(real),benv(syn); ref=max(R.max(),S.max())
    fig,ax=plt.subplots(1,3,figsize=(17,4))
    t=np.arange(R.shape[1])*220/SR
    for i,(a,b) in enumerate(BANDS):
        c=f'C{i}'; ax[0].plot(t,R[i]-ref,c,label=f'{a}-{b}'); ax[0].plot(np.arange(S.shape[1])*220/SR,S[i]-ref,c+'--')
    ax[0].set_ylim(-80,3); ax[0].legend(fontsize=7); ax[0].set_title(name+' band env (solid real, dashed synth)')
    n=int(0.08*SR); ax[1].plot(np.arange(n)/SR*1000,real[:n],lw=.8,label='real'); ax[1].plot(np.arange(n)/SR*1000,syn[:n],lw=.8,alpha=.8,label='synth'); ax[1].legend(); ax[1].set_title('first 80 ms')
    for x,l in ((real,'real'),(syn,'synth')):
        L=min(len(x),SR); sp=20*np.log10(np.abs(np.fft.rfft(x[:L]*np.hanning(L),1<<17))+1e-9); f=np.fft.rfftfreq(1<<17,1/SR)
        ax[2].semilogx(f,sp-sp.max(),lw=.6,label=l)
    ax[2].set_xlim(30,18000); ax[2].set_ylim(-90,2); ax[2].legend(); ax[2].set_title('spectrum first 1 s')
    plt.tight_layout(); plt.savefig(path,dpi=65); plt.close()
