# -*- coding: utf-8 -*-
from pylab import np, plt, mpl
import control

def get_coeffs_dc_motor_current_regulator(R, L, Bandwidth_Hz):
    Kp = Bandwidth_Hz * 2 * np.pi * L
    Ki = R / L
    return Kp, Ki

def get_coeffs_dc_motor_SPEED_regulator(J_s, n_pp, KE, delta, currentBandwidth_radPerSec):
    speedKi = currentBandwidth_radPerSec / delta**2
    speedKp = J_s/n_pp / (1.5*n_pp*KE) * delta * speedKi
    return speedKp, speedKi

def 逆上位机速度PI系数转换CODE(iSMC_speedKp, iSMC_speedKiCode, VL_TS, J_s):
    上位机速度KP = iSMC_speedKp / (2*np.pi * J_s)
    iSMC_speedKi = iSMC_speedKiCode/iSMC_speedKp/VL_TS
    上位机速度KI = iSMC_speedKi / (上位机速度KP * np.pi/2) * 1000
    return 上位机速度KP, 上位机速度KI

def 上位机速度PI系数转换CODE(上位机速度KP, 上位机速度KI, VL_TS, J_s):
    # 源代码
        # Kvp_in = 上位机速度KP
        # Kvi_in = 上位机速度KI/1000 * kvp_in * np.pi/2
        # iSMC_speedKp = kvp_in * 2*np.pi * J_s
        # iSMC_speedKi = iSMC_speedKp * kvi_in * VL_TS
    # 简洁点：
    iSMC_speedKp = 上位机速度KP * 2*np.pi * J_s
    iSMC_speedKi = 上位机速度KI/1000 * 上位机速度KP * np.pi/2
    iSMC_speedKiCode = iSMC_speedKi * iSMC_speedKp  * VL_TS
    return iSMC_speedKp, iSMC_speedKi, iSMC_speedKiCode

# current reference to current measurement
def c2c_design(R, L, BW_current_Hz=1000, CL_TS=1/20e3):
    currentKp, currentKi = get_coeffs_dc_motor_current_regulator(R, L, BW_current_Hz)
    currentKiCode = currentKi * currentKp * CL_TS
    if True:
        # 这里打印的用于实验中CCS的debug窗口检查电流环PI系数
        上位机电流KP = BW_current_Hz
        上位机电流KI = 1000
        iSMC_currentKp = 上位机电流KP * L * 2*np.pi
        iSMC_currentKi = 上位机电流KI/1000 * R/L
        iSMC_currentKiCode = iSMC_currentKi * CL_TS * iSMC_currentKp
        print(f'\tiSMC_currentKp={iSMC_currentKp:g}, \
                  iSMC_currentKi={iSMC_currentKi:g}, \
                  iSMC_currentKiCode={iSMC_currentKiCode:g}')
        print(f'\tSimC_currentKp={currentKp:g}, \
                  SimC_currentKi={currentKi:g}, \
                  SimC_currentKiCode={currentKiCode:g}')
        print(f'\t上位机电流KP={上位机电流KP:g}, \
                  上位机电流KI={上位机电流KI:g}')
    Gi_closed = control.tf([1], [L/currentKp, 1]) # current loop zero-pole cancelled already
    currentBandwidth_radPerSec = currentKp/L

    # 注意，我们研究的开环传递函数是以电流给定为输入的，而不是以转速控制误差为输入，这样仿真和实验容易实现一点。
    c2c_tf = Gi_closed

    # fig5 = plt.figure(fignum)
    # plt.title('Designed Current Ref. to Velocity Meas. Transfer Function')
    mag, phase, omega = control.bode_plot(c2c_tf, 2*np.pi*np.logspace(0,4,500), dB=1, Hz=1, deg=1, lw='0.5', label=f'{BW_current_Hz:g} Hz')
    open_cutoff_frequency_HZ = omega[(np.abs(mag-0.0)).argmin()]/2/np.pi
    # print('\tCut-off frequency (without speed PI regulator):', open_cutoff_frequency_HZ, 'Hz')
    return  (currentKp, currentKi), \
            (上位机电流KP, 上位机电流KI), \
            (mag, phase, omega)

# current reference to velocity measaurement (this is not velocity open loop, because speed PI is not considered)
def c2v_design(R, L, n_pp, J_s, KE, B=0, BW_current_Hz=1000, CL_TS=1/20e3, fignum=5):

    currentKp, currentKi = get_coeffs_dc_motor_current_regulator(R, L, BW_current_Hz)
    currentKiCode = currentKi * currentKp * CL_TS
    if True:
        # 这里打印的用于实验中CCS的debug窗口检查电流环PI系数
        上位机电流KP = BW_current_Hz
        上位机电流KI = 1000
        iSMC_currentKp = 上位机电流KP * L * 2*np.pi
        iSMC_currentKi = 上位机电流KI/1000 * R/L
        iSMC_currentKiCode = iSMC_currentKi * CL_TS * iSMC_currentKp
        print(f'\tiSMC_currentKp={iSMC_currentKp:g}, \
                  iSMC_currentKi={iSMC_currentKi:g}, \
                  iSMC_currentKiCode={iSMC_currentKiCode:g}')
        print(f'\tSimC_currentKp={currentKp:g}, \
                  SimC_currentKi={currentKi:g}, \
                  SimC_currentKiCode={currentKiCode:g}')
        print(f'\t上位机电流KP={上位机电流KP:g}, \
                  上位机电流KI={上位机电流KI:g}')
    Gi_closed = control.tf([1], [L/currentKp, 1]) # current loop zero-pole cancelled already
    currentBandwidth_radPerSec = currentKp/L

    KT = 1.5*n_pp*KE
    dc_motor_motion = control.tf([KT], [J_s/n_pp, B]) # [Apk] to [elec.rad/s]
    print(dc_motor_motion)
    # quit()

    # 注意，我们研究的开环传递函数是以电流给定为输入的，而不是以转速控制误差为输入，这样仿真和实验容易实现一点。
    # Gw_open = dc_motor_motion * Gi_closed * speedPI
    c2v_tf = dc_motor_motion * Gi_closed

    # fig5 = plt.figure(fignum)
    # plt.title('Designed Current Ref. to Velocity Meas. Transfer Function')
    mag, phase, omega = control.bode_plot(c2v_tf, 2*np.pi*np.logspace(0,4,500), dB=1, Hz=1, deg=1, lw='0.5', label=f'{BW_current_Hz:g} Hz')
    open_cutoff_frequency_HZ = omega[(np.abs(mag-0.0)).argmin()]/2/np.pi
    # print('\tCut-off frequency (without speed PI regulator):', open_cutoff_frequency_HZ, 'Hz')
    return  (currentKp, currentKi), \
            (上位机电流KP, 上位机电流KI), \
            (mag, phase, omega)

# velocity reference to velocity measaurement
def iterate_for_desired_bandwidth( delta, desired_BW_velocity_HZ, BW_current_Hz_initial=1000, BW_Current_Hz_Step_Size=100):

    R          = motor_dict['Rs']
    L          = motor_dict['Lq']
    J_s        = motor_dict['J_s']
    JLoadRatio = motor_dict['JLoadRatio']
    n_pp       = motor_dict['n_pp']
    KE         = motor_dict['KE']
    CL_TS      = motor_dict['CL_TS']
    VL_TS      = motor_dict['VL_TS']
    J_total = J_s*(1+JLoadRatio) 

    BW_current_Hz = BW_current_Hz_initial  #100 # Hz (initial)
    BW_velocity_HZ = 0  # Hz (initial)
    count = 0
    while True:
        count += 1
        if count>20:
            msg = f'Loop count 20 is reached. Step size is {BW_Current_Hz_Step_Size} Hz.'
            print(msg)
            # raise Exception()
            break

        # Current loop (Tune its bandwidth to support required speed response)
        if abs(BW_velocity_HZ - desired_BW_velocity_HZ)<=10: # Hz
            break
        else:
            if BW_velocity_HZ > desired_BW_velocity_HZ:
                BW_current_Hz -= BW_Current_Hz_Step_Size # Hz
                if BW_current_Hz<=0:
                    raise Exception(f'Negative BW_current_Hz. Maybe change the step size of "BW_current_Hz" ({BW_Current_Hz_Step_Size} Hz) and try again.')
                    break
            else:
                BW_current_Hz += BW_Current_Hz_Step_Size # Hz
        print(f'BW_current_Hz = {BW_current_Hz}')

        currentKp, currentKi = get_coeffs_dc_motor_current_regulator(R, L, BW_current_Hz)
        currentKiCode = currentKi * currentKp * CL_TS
        if True:
            # 这里打印的用于实验中CCS的debug窗口检查电流环PI系数
            上位机电流KP = BW_current_Hz
            上位机电流KI = 1000
            iSMC_currentKp = 上位机电流KP * L * 2*np.pi
            iSMC_currentKi = 上位机电流KI/1000 * R/L
            iSMC_currentKiCode = iSMC_currentKi * CL_TS * iSMC_currentKp
            print(f'\tiSMC_currentKp={iSMC_currentKp:g}, \
                      iSMC_currentKi={iSMC_currentKi:g}, \
                      iSMC_currentKiCode={iSMC_currentKiCode:g}')
            print(f'\tSimC_currentKp={currentKp:g}, \
                      SimC_currentKi={currentKi:g}, \
                      SimC_currentKiCode={currentKiCode:g}')
            print(f'\t上位机电流KP={上位机电流KP:g}, \
                      上位机电流KI={上位机电流KI:g}')
        Gi_closed = control.tf([1], [L/currentKp, 1]) # current loop zero-pole cancelled already
        currentBandwidth_radPerSec = currentKp/L

        # Speed loop
        KT = 1.5*n_pp*KE
        dc_motor_motion = control.tf([KT*n_pp/J_total], [1, 0])
        speedKp, speedKi = get_coeffs_dc_motor_SPEED_regulator(J_total, n_pp, KE, delta, currentBandwidth_radPerSec)
        speedKiCode = speedKi * speedKp * VL_TS
        if True:
            # 这里打印的用于实验中TI的debug窗口检查系数

            上位机速度KP, 上位机速度KI = 逆上位机速度PI系数转换CODE(speedKp, speedKiCode, VL_TS, J_total)

            iSMC_speedKp, iSMC_speedKi, iSMC_speedKiCode = 上位机速度PI系数转换CODE(上位机速度KP, 上位机速度KI, VL_TS, J_total)

            print(f'\tiSMC_speedKp={iSMC_speedKp:g}, \
                      iSMC_speedKi={iSMC_speedKi:g}, \
                      iSMC_speedKiCode={iSMC_speedKiCode:g}')
            print(f'\tSimC_speedKp={speedKp:g}, \
                      SimC_speedKi={speedKi:g}, \
                      SimC_speedKiCode={speedKiCode:g}')
            print(f'\t上位机速度KP={上位机速度KP:g}, \
                      上位机速度KI={上位机速度KI:g}')
        # 下面打印的用于仿真
        print(f'\tspeedKp = {speedKp:g}', f'speedKi = {speedKi:g}', \
              f'wzero = {speedKi/2/np.pi:g} Hz', \
              f'cutoff = {delta*speedKi/2/np.pi:g} Hz', \
              f'ipole = {currentKp/L/2/np.pi:g} Hz', sep=' | ')

        speedPI = control.tf([speedKp, speedKp*speedKi], [1, 0])
        Gw_open = dc_motor_motion * Gi_closed * speedPI
        Gw_closed = Gw_open / (1+Gw_open)
        # print(Gw_closed)

        fig5 = plt.figure(fignum)
        plt.title('Designed Velocity Ref. to Velocity Meas. Transfer Function')
        mag, phase, omega = control.bode_plot(Gw_closed, 2*np.pi*np.logspace(0,4,500), dB=1, Hz=1, deg=1, lw='0.5', label=f'{delta:g}')
        BW_velocity_HZ = omega[(np.abs(mag-0.707)).argmin()]/2/np.pi
        print('\tSpeed loop bandwidth:', BW_velocity_HZ, 'Hz')
    return  (currentKp, currentKi), \
            (speedKp, speedKi), \
            (上位机电流KP, 上位机电流KI), \
            (上位机速度KP, 上位机速度KI), \
            (mag, phase, omega)

if __name__ == '__main__':
    # 伺尔沃400W
    R = 0.152    # Ohm
    L = 0.466e-3 # H
    J_s  = 0.160*1e-4 # kg.m^2
    KE =  0.023331 #0.0117246 # Vs
    n_pp = 4 


    # Iterate for a preset speed loop bandwidth based on your delta value

    # Pick your favorite step repsonse by "shape" via damping factor \delta
    delta = 6.5

    # Specify your desired speed closed-loop bandwidth
    desired_BW_velocity_HZ = 100

    currentPI, speedPI, _, _, _ = iterate_for_desired_bandwidth(delta, desired_BW_velocity_HZ, R, L, J_s, n_pp, KE)
    currentKp, currentKi = currentPI
    speedKp, speedKi = speedPI

    mpl.rcParams['figure.dpi'] = 200
    plt.style.use('ggplot')

    fig5 = plt.figure(5)
    fig5.axes[0].set_ylim([-3, 10]) # -3dB
    fig5.axes[1].set_ylim([-90, 0]) # 90 deg
    print(f'\
        #define CURRENT_KP {currentKp:g}\n\
        #define CURRENT_KI {currentKi:g}\n\
        #define CURRENT_KI_CODE (CURRENT_KI*CURRENT_KP*CL_TS)\n\
        #define SPEED_KP {speedKp:g}\n\
        #define SPEED_KI {speedKi:g}\n\
        #define SPEED_KI_CODE (SPEED_KI*SPEED_KP*VL_TS)\n')
    plt.show()