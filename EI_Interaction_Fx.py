'''
Closed-form solution for calculating EI via the Multiple Inline Interacting Cantilever Beam Model
Author: Austin Bebee
Last updated: 7/6/2020

Require input values for peak force (f), force bar height (h), beam length (l), beam-to-beam spacing (s).

Assumes the system contains the full/max number of beams (full interaction) at the first beam's max deflection.
If this is not the case, set the variable "finite_beam_num" to True and set the variable "beam-num" to the number
of beams in a row.
Additional assumptions:
    - beams deflect linearly inline
    - force bar force always perpendicular to 1st beam's end angle
    - each beam has same K & KO
'''

# Required libraries
import numpy as np
import math

# INPUT PARAMETERS. EI will be calculated in units of f*(l^2)
# example
#f = 5  # peak force
#h = 8  # force bar height
#l = 10  # beam length
#s = 1  # beam-to-beam spacing
definite_beam_num = False  # if False, assumes max number of beams (full interaction) at the first beam's max deflection
beams = 8  # num. of beams in a row (only used if "definite_beam_num" set to True)

# Model lists/arrays - each index is a beam's attribute (0 index = 1st beam, last index = last beam)
theta = list()  # PRBM angle (radians)
beta = list()  # math.pi/2 - theta (radians)
x = list()  # x deflection
d = list()  # horizontal distance a beam extends past the next (x - s)
phi = list()  # force vector angle w/ respect to undeflected axis (vertical axis in this case)
forces = list()  # individual reaction forces
q = list()  # effective beam lengths
KO = list()  # stiffness coefficient
gl = list()  # gamma*l (longer rigid link length)

def clearAll(): # Clears variables for new simulation
    beta.clear()
    x.clear()
    d.clear()
    phi.clear()
    forces.clear()
    q.clear()
    KO.clear()
    gl.clear()

def MultiPhiCor(h, l, s, phi): # Phi correctoin for multiple beams (exp. developed) used when h/l < 0.7
    if h/l < 0.7:
        mphi = 244.7802*(s/l) - 683.4973*((s/l)**2) - 165.1557*((s/l)*(h/l)) + 43.4227*((h/l)**2)
        mphi = mphi * ((math.pi) / 180)
    else:
        mphi = phi

    return mphi

def Parametric_angle_coefficient(n): # returns c (parametric angle coefficient) when given n
    if -4 < n <= -1.5:
        c = 1.238945 + 0.012035*n + 0.00454*(n**2)
    elif -0.5 < n: # <= 10: # some conditions yield n = 10.25, which is just beyond the defined limits of n. Can either remove n <= 10 boundary or set n = 10 if n > 10.
        c = 1.238845 + 0.009113*n - 0.001929*(n**2) + 0.000191*(n**3) - 0.000007*(n**4)
    return c

def gammaUpdate(n):# returns gamma value when give n
    if n > .5: # <= 10: # some conditions yield n = 10.25, which is just beyond the defined limits of n. Can either remove n <= 10 boundary or set n = 10 if n > 10.
        gamma = .841655 - 0.0067807 * n + .000438 * (n ** 2)
    elif n > -1.8316 and n < 0.5:
        gamma = .852144 - 0.0182867 * n
    elif n > -5 and n < -1.8316:
        gamma = .912364 + .0145928 * n

    return gamma

def KOupdate(n):# returns Ko (stiffness coefficient) when given n
    if n > -5 and n <= -2.5:
        Ko = (3.024112 + 0.121290 * n + 0.003169 * (n ** 2))
    elif n > -2.5 and n <= -1:
        Ko = (1.967647 - 2.616021 * n - 3.738166 * (n ** 2) - 2.649437 * (n ** 3) - 0.891906 * (n ** 4) - 0.113063 * (n ** 5))
    elif n > -1: # and n <= 10: # <= 10: # some conditions yield n = 10.25, which is just beyond the defined limits of n. Can either remove n <= 10 boundary or set n = 10 if n > 10.
        Ko = (2.654855 - 0.509896 * (10 ** -1) * n + 0.126749 * (10 ** -1) * (n ** 2) - 0.142039 * (10 ** -2) * (n ** 3) + 0.584525 * (10 ** -4) * (n ** 4))

    return Ko

# MAIN FUNCTION THAT RETURNS THE SYSTEM'S MEAN EI
def EI_Interaction(f, h, l, s):

    ## DETERMINE 1ST BEAM'S KINEMATICS ##

    #initial assumption that force bar applies a horizontal force yields:
    n = 0 # initial n value
    gamma = gammaUpdate(n)  # initial gamma

    # Gamma Convergence Cycle - update gamma for better estimate
    j = 0
    while j < 100:  # gamma converges well before 100 iterations
        b = (1 - gamma) * l  # length below torsional spring (in.)
        betaV = (np.arcsin((h - b) / (gamma * l)))  # beta angle value (rads)
        thetaV = (math.pi / 2) - betaV  # PRBM theta value (rads)
        c = Parametric_angle_coefficient(n)  # get parametric angle coefficient
        beam_end_angle = thetaV * c  # corrected beam end angle
        phiV = (math.pi / 2) - beam_end_angle  # phi value (perpendicular to beam end angle)
        n = (1 / np.tan(phiV))  # update n
        #  Option below: if n > 10 (beyond PRBM defined limits) set n = 10 (note: negligible change if used)
        #if n > 10:
         #   n = 10
        gamma = gammaUpdate(n)  # update gamma
        j += 1
    
    b1 = b # stores final b of 1st beam
    gamma1 = gamma  # stores final gamma of 1st beam

    # 1st beam's geometry & attributes:
    q.insert(0, l)  # effective beam length
    gl.insert(0, gamma * l)  # stores longer rigid link length
    Ko = KOupdate(n)  # update Ko (stiffness coefficient)
    KO.insert(0, Ko)  # stores 1st beam's stiffness coefficient
    beta.insert(0, betaV)  # stores beta angle
    x.insert(0, gl[0] * np.cos(beta[0]))  # stores x deflection
    d.insert(0, x[0] - s)  # stores horizontal distance beam extends past the next

    phiCorrection = MultiPhiCor(h, l, s, phiV) # correct phi (if h/l < 0.7)
    phi.insert(0, phiCorrection)  # force vector angle w/ respect to undeflected axis

    # ALL OTHER BEAM'S KINEMATICS
    def otherBeams(i): # called after determining # of beams
        beta.insert(i + 1, np.arctan((gl[i] * np.sin(beta[i])) / d[i]))
        phiV = (beta[i])  # initially assume phi = previous beta
        n = (1 / np.tan(phiV))  # determine n
        c = Parametric_angle_coefficient(n) # determine c
        phiV = (math.pi / 2) - (math.pi / 2 - beta[i]) * c # correct & update phi
        phiCorrection = MultiPhiCor(h, l, s, phiV) # correct phi (if h/l < 0.7)
        phi.insert(i + 1, phiCorrection) # store beam's phi
        Ko = KOupdate(n)  # update Ko
        KO.insert(i+1, Ko)  # store beam's Ko
        gamma = gammaUpdate(n)  # update gamma
        b = (1 - gamma) * l  # update base length
        q.insert(i + 1, b + math.sqrt(d[i] ** 2 + (gl[i] * np.sin(beta[i])) ** 2))  # effective cantilever beam length (base to applied force from previous beam or force bar)
        gl.append(gamma * l)  # store beam's gamma*length  
        x.insert(i + 1, gl[i + 1] * np.cos(beta[i + 1]))  # x deflection at end of beam
        #y.insert(i+1, gl[i+1] * np.sin(beta[i + 1])) # y deflection at end of beam (not needed for EI calculation)
        d.insert(i + 1, x[i + 1] - s)# stores horizontal distance beam extends past the next


        return d[i]  # returns distance to check to continue looping or not

    # Determine # of other beams:
    if definite_beam_num == False:  # full interaction @ 1st beam's max deflection
        i = 0
        while d[i] > 0:  # will previous beam hit next beam? If so, run that beam through otherBeams()
            otherBeams(i)
            i += 1
    else:  # definite number of beams in a row (may not be full/max interaction possible)
        i = 0
        while d[i] > 0 and i < beams-1:  # will previous beam hit next beam & does that beam exist? If so, run that beam through otherBeams()
            otherBeams(i)
            i += 1

    # BACKSOLVE TO GET ALL FORCES/K EXCEPT 1ST FORCE/K

    # Last beam force/k
    if len(beta) > 1:  # check if more than 1 beam
        num = ((math.pi / 2) - beta[-1])  # numerator = theta
        den = ((x[-2] - s) * np.cos(phi[-1]) + (gl[-2] * np.sin(beta[-2]) * np.sin(phi[-1])))  # denominator
        forces.insert(-1, num / den)  # last force/k
    else:  # if only one beam, skip
        pass

    # middle beam forces/k
    j = -2
    if len(beta) > 1:  # check if more than 1 beam
        while j > -(len(beta)):  # loop until reaching 1st force/K
            num1 = ((math.pi / 2) - beta[j])  # 1st numerator term = theta
            num2 = forces[j + 1] * (gl[j] * np.sin(beta[j]) * np.sin(phi[j + 1]) + x[j] * np.cos(phi[j + 1]))  # force due to previous beam
            den1 = (x[j - 1] - s) * np.cos(phi[j])  # denominator term 1
            den2 = gl[j - 1] * np.sin(beta[j - 1]) * np.sin(phi[j])  # denominator term 2
            forces.insert(j, (num1 + num2) / (den1 + den2))  # forces/k

            j = j - 1  # increment backwards

    # 1st Beam calculations
    fx = f / np.sin(phi[0])
    forces.insert(0, fx)  # store force bar applied force in 0 index
    
    # calculate K (torsional spring constant) of 1st beam
    knum1 = fx * (x[0] * np.cos(phi[0]) + (h - b1) * np.sin(phi[0]))  # numerator
    kden1 = ((math.pi / 2) - beta[0])  # denominator 1st term

    if len(beta) > 1:  # if more than 1 beam (i.e., interacting beams)
        kden2 = forces[1] * ((h - b1) * np.sin(phi[1]) + x[0] * np.cos(phi[1])) # denominator 2nd term due to interactions
    else: # only 1 beam, no interactions
        kden2 = 0

    K = (knum1) / (kden1 + kden2)  # compute K (torsional spring constant)

    ## COMPUTE EI ##
    EI = (l * K) / (KO[0] * gamma1)

    #t_num = len(beta)  # total number of interacting beams @ 1st beam's deflection
    
    return EI

def test(f, h, l, s):
    clearAll()
    EI = EI_Interaction(f, h, l, s)
    print(EI)

#test(7, 5, 10, 1)
