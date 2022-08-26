'''
No-Interaction Closed-form solution for calculating EI via the Multiple Inline Non-Interacting Cantilever Beam Model
Author: Austin Bebee
Last updated: 7/6/2020

Require input values for peak force (f), force bar height (h), beam length (l), beam-to-beam spacing (s).

Assumes the system contains the full/max number of beams at the first beam's max deflection.
If this is not the case, set the variable "finite_beam_num" to True and set the variable "beam-num" to the number
of beams in a row.
Additional assumptions:
    - no contact between beams. Beams only contact the force bar
    - force bar force always perpendicular to 1st beam's end angle
    - each beam may have different K & KO
'''

# Required libraries
import numpy as np
import math

# INPUT PARAMETERS (EI will be calculated in units of f*l^2)
# f = 5 # peak force
# h = 8 # force bar height
# l = 10 # beam length
# s = 1 # beam-to-beam spacing
definite_beam_num = False # # if False, assumes max number of beams at the first beam's max deflection
beams = 8 # num. of beams in a row (only used if "definite_beam_num" set to True)

# Model lists/arrays - each index is a beam's attribute (0 index = 1st beam, last index = last beam)
theta = list() # PRBM angle (rads)
beta = list() # math.pi/2 - theta (rads)
x = list() # x deflection
d = list() # horizontal distance a beam extends past the next (x - s)
phi = list() # 180 deg. - alpha
q = list()# effective l term in following k's equation 
KO = list() # stiffness coefficient
gl = list() # gamma*l (longer rigid link length)
dens = list() # denominator terms for EI

def clearAll(): # clears variables for new simulation 
    beta.clear()
    theta.clear()
    x.clear()
    d.clear()
    phi.clear()
    q.clear()
    KO.clear()
    gl.clear()
    dens.clear()

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
def EI_NoInteraction(f, h, l, s):

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
    gamma1 = gamma # stores final gamma of 1st beam
    
    # 1st beam's geometry & attributes:
    q.insert(0, l)  # effective beam length
    gl.insert(0, gamma1 * l)  # stores longer rigid link length
    Ko = KOupdate(n)  # update Ko (stiffness coefficient)
    KO.insert(0, Ko)  # stores 1st beam's stiffness coefficient
    beta.insert(0, betaV)  # stores beta angle
    x.insert(0, gl[0] * np.cos(beta[0]))  # stores x deflection
    d.insert(0, x[0] - s)  # stores horizontal distance beam extends past the next
    phi.insert(0, phiV)  # force vector angle w/ respect to undeflected axis

    # ALL OTHER BEAM'S KINEMATICS
    i = 0
    def otherBeams(i): # called after determining # of beams
        beta.insert(i+1, np.arctan((gl[0] * np.sin(beta[0])) / (d[i])))
        phiV = beta[i] # initialy assum phi = previous beta
        n = (1/np.tan(phiV)) # determine n
        c = Parametric_angle_coefficient(n) # get parametric angle coefficient 
        phiV = (math.pi / 2) - (math.pi / 2 - beta[i]) * c # correct & update phi
        phi.insert(i+1, phiV) # store beam's phi
        Ko = KOupdate(n) # update Ko
        KO.insert(i+1, Ko) # store Ko
        gamma = gammaUpdate(n) # update gamma
        gl.append(gamma * l) # store g*l
        b = ((1 - gamma) * l) # update base length
        x.insert(i+1, d[i]) # x distance from base of beam to force bar's positon @ 1st beam's max deflection
        d.insert(i+1, x[i+1] - s) # horizontal distance beam extends past the next
        q.insert(i+1, b + math.sqrt(x[i]**2 + (gl[0]*np.sin(beta[0]))**2)) # effective cantilever beam length (base to applied force)

        return i

    # Determine # of other beams:
    numBeams = int(round(x[0]/s)) # number of additional beams hitting force bar at 1st one's max deflection
    
    if definite_beam_num == False:  # full number of beams @ 1st beam's max deflection
        i = 0 
        while i <= (numBeams-2):  # will beam hit force bar? If so, run that beam through otherBeams()
        # numBeams - 2: -2 because 1st beam already computed, i starts at 0
            otherBeams(i)
            i += 1
    else:  # definite number of beams in a row (may expect more beams than the system actually has)
        i = 0
        while i <= (numBeams-2) and i < beams-1:  # will beam hit force bar & does that beam exist? If so, run that beam through otherBeams()
            otherBeams(i)
            i += 1
            
    # Calculations required to compute EI
    for i in range(len(beta)):
        theta.insert(i, ((math.pi/2)-beta[i])) # PRBM Theta
        #s.insert(i, deltaTheta[i]/(gamma*(q[i]**2)))                     
        dens.insert(i, (KO[i]*theta[i])/(q[i]**2)) # denominator terms for EI
    EIden = sum(dens) # denominator sum term for EI
    # Compute EI
    Ftot = f/np.sin(phi[0]) # estimate F total from Fx 
    EI = Ftot/EIden

    return EI
    
def test(f, h, l, s):
    clearAll()
    EI = EI_NoInteraction(f, h, l, s)
    print(EI)

#test(5, 8, 10, 1)
