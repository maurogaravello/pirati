#!/usr/bin/env python

import numpy
import scipy.signal
import pde
import ode
import save

#
# function for solving the system in a one temporal step 
# 
def one_step_evolution(p_density, s_density, police, xx, yy,
                       p_kernel, cut_off, dx, dy, dt, kappa, a,
                       velocity, nu_x, nu_y):
    """
    This function performs a one time step evolution for the whole system

    :param p_density: numpy 2d array describing the density of pirates at time t
    :param s_density: numpy 2d array describing the density of ships at time t
    :param police: list containing the position of police
    :param xx: numpy 2d array describing the x-mesh. Same shape as p_density
               and s_density
    :param yy: numpy 2d array describing the y-mesh. Same shape as p_density
               and s_density
    :param p_kernel: numpy 2d array describing the kernel in the equation for
                     pirates. Same shape as p_density
    :param cut_off: cut_off function.
    :param dx: float. The size of the x-mesh
    :param dy: float. The size of the y-mesh
    :param dt: float. The time step. It should satisfy a stability condition
    :param kappa: function. It takes a numpy array and returns an arry of the same shape. It is the normalized function in the equation for pirates
    :param a: array of floats. Coefficients a for the source term f in the equation for pirates.
    :param velocity: function describing the speed of the ship.
    :param nu_x: x-direction of the geometric component of nu
    :param nu_y: x-direction of the geometric component of nu

    The output is a tuple (p_new, s_new, police_new) of three elements.
    :output p_new: numpy 2d array of the same shape as p_density
                   describing the density of pirates at time t + dt
    :output s_new: numpy 2d array of the same shape as s_density
                   describing the density of ships at time t + dt
    :output police_new: list of final position of police vessels
    """
    # some checks
    shape_p_density = numpy.shape(p_density)
    assert (shape_p_density == numpy.shape(s_density))
    assert (shape_p_density == numpy.shape(xx))
    assert (shape_p_density == numpy.shape(yy))
    assert (shape_p_density == numpy.shape(yy))

    # Calculus of common terms ?
    police_sum_x = sum(i[0] for i in police)
    police_sum_y = sum(i[1] for i in police)
    M = len(police)
    
    ################################
    # Evolution of pirate density
    ################################

    # 2d convolution on a fixed mesh
    # h * k [n, m] = dx * dy * convolve2d(h, k)
    p_convolution = dx * dy * scipy.signal.convolve2d(s_density, p_kernel, mode='same')
    # gradient of the convolution
    grad_py, grad_px = numpy.gradient(p_convolution, dy, dx)
    # norm of the gradient
    norm_grad_p_convolution = numpy.sqrt(grad_px**2 + grad_py**2)
    flux_x = kappa(norm_grad_p_convolution) * grad_px * p_density
    flux_y = kappa(norm_grad_p_convolution) * grad_py * p_density
    # divergence
    trash, div1 = numpy.gradient(flux_x, dy, dx)
    div2, trash = numpy.gradient(flux_y, dy, dx)
    div = - div1 - div2

    
    # term depending on the police
    f = numpy.zeros_like(xx)
    for i in xrange(len(police)):
        f += a[i] * cut_off(xx - police[i][0], yy - police[i][1])


    p_new = pde.one_step_parabolic(p_density, xx, yy, div, -f, dx, dy, dt)

    ################################
    # Evolution of ship density
    ################################

    # 2d convolution on a fixed mesh
    # h * k [n, m] = dx * dy * convolve2d(h, k)
    cal_I1_x = - dx * dy * scipy.signal.convolve2d(p_density, xx * cut_off(xx, yy), mode='same')
    cal_I1_y = - dx * dy * scipy.signal.convolve2d(p_density, yy * cut_off(xx, yy), mode='same')

    cal_I2_x = numpy.zeros_like(xx)
    cal_I2_y = numpy.zeros_like(xx)
    for i in xrange(len(police)):
        cal_I2_x += cut_off(xx - police[i][0], yy - police[i][1]) * (police[i][0] - xx)
        cal_I2_y += cut_off(xx - police[i][0], yy - police[i][1]) * (police[i][1] - yy)

    cal_I_x = cal_I1_x + cal_I2_x
    cal_I_y = cal_I1_y + cal_I2_y
    vel_x = cal_I_x + nu_x
    vel_y = cal_I_y + nu_y
    s_new = pde.one_step_hyperbolic(s_density, velocity, vel_x, vel_y, dx, dy, dt)


    ################################
    # Evolution of police position
    ################################

    police_new = []
    for i in xrange(len(police)):
        temp = cut_off(police[i][0] - xx, police[i][1] - yy) * p_density * s_density
        F1_x = dx * dy * numpy.sum(temp * (xx - police[i][0]))
        F1_y = dx * dy * numpy.sum(temp * (yy - police[i][1]))

        # F1_x = dx * dy * scipy.signal.convolve2d(p_density * s_density, -temp * (xx - police[i][0]), mode = 'same')
        # F1_y = dx * dy * scipy.signal.convolve2d(p_density * s_density, -temp * (yy - police[i][1]), mode = 'same')

        F2_x = police_sum_x - M * police[i][0]
        F2_y = police_sum_y - M * police[i][1]

        F3_x = 0.   #control_x
        F3_y = 0.   #control_y
        
        police_new.append(ode.ode(F1_x + F2_x + F3_x, F1_y + F2_y + F3_y, police[i], dt))



    return (p_new, s_new, police_new)




#
# function for solving the system
# 
# def evolution(p_density, s_density, police, xx, yy,
#                        p_kernel, cut_off, dx, dy, dt):
def evolution(pirates):
    """
    This function performs the evolution for the whole system

    :param pirates: pirate class

    The output is a tuple (p_new, s_new, police_new) of three elements.
    :output p_new: numpy 2d array of the same shape as p_density
                   describing the density of pirates at time t + dt
    :output s_new: numpy 2d array of the same shape as s_density
                   describing the density of ships at time t + dt
    :output police_new: list of final position of police vessels
    """

    p_density = pirates.initial_density_pirates
    s_density = pirates.initial_density_ships
    police = pirates.police_initial_positions

    print_number = 1
    for i in xrange(1, len(pirates.time)):

        # evolution from t to t + dt
        (p_density, s_density, police) = one_step_evolution(p_density, s_density, police, pirates.x_mesh, pirates.y_mesh,
                                                            pirates.kernel_mathcal_K, pirates.cut_off_C, pirates.dx, pirates.dy, pirates.dt, pirates.kappa, pirates.a, pirates.ships_speed, pirates.ships_direction(pirates.x, pirates.y)[0], pirates.ships_direction(pirates.x, pirates.y)[1])

        # printing
        if pirates.printing[i]:
            # if True:
            name = 'saving_' + str(print_number).zfill(4)
            save.solution_Save(pirates.base_directory, name, pirates.time[i], p_density, s_density, police)
            print_number += 1

        
