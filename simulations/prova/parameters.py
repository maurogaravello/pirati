# parameters for pirates - 

######################################################
## DOMAIN \Omega = (x_1, x_2) x (y_1, y_2)
######################################################

x_1 = 0. # minimum value for x
x_2 = 10. # maximum value for x

y_1 = 0. # minimum value for y
y_2 = 20. # maximum value for y

######################################################
## MESH SIZES
## n_x = number of cells in the x-direction
## n_y = number of cells in the y-direction
######################################################

n_x = 200 # integer
n_y = 100 # integer


######################################################
## TIME of simulation
######################################################

tMax = 10. # time of simulation

######################################################
## EQUATION FOR rho (pirates)
######################################################

# Initial Datum for rho (density of piracy)
def InitialDatum_rho (x, y):
    return x*y

# normalization function kappa
def kappa(x):
    eps = 0.2
    v_max = 1.

    A1 = (x >= 1) * x + (x < 1) * 1
    A2 = v_max * (x < 1) * 0 / A1
    A3 = v_max * numpy.logical_and(x > eps, x < 1) * (x - eps) / (1 - eps)
    
    return A2 + A3

# coefficients a_i for definition of f (len = M)
a = [1., 1.5, 2.] 


######################################################
## EQUATION FOR A (ships)
######################################################

# Initial Datum for A (density of ships)
def InitialDatum_A (x, y):
    A1 = numpy.logical_and(2 <= x, x <=4) * numpy.ones_like(x) * numpy.logical_and(2 <= y, y <=4) * numpy.ones_like(y)
    A2 = numpy.logical_and(2 <= x, x <=4) * numpy.ones_like(x) * numpy.logical_and(8 <= y, y <=12) * numpy.ones_like(y)
    return A1 + A2

# speed of ships
def speed_ships(A):
    A_max = 1. # maximum density
    v_max = 1. # maximum speed
    return v_max - A/A_max

# geometric vector speed
def nu(x,y):
    x_mesh, y_mesh = numpy.meshgrid(x, y)
    nu_x = numpy.ones_like(x_mesh + y_mesh)
    nu_y = numpy.zeros_like(x_mesh + y_mesh)

    return (nu_x, nu_y)


######################################################
## EQUATION FOR d (police vessels)
######################################################

# Number M of police vessels
M = 3 # integer number

# Initial Datum for police vessels
# d_o -> list of size M
# each element is a tuple with 2 elements
d_o = [(5., 11.), (2., 10.), (7., 10.)] 



#######################################################
## Various kernels and cut-off
#######################################################

# Standard mollifier
def std_moll(x, y, radius = 1.):
    x_mesh, y_mesh = numpy.meshgrid(x, y)
    # k = (x_mesh**2 + y_mesh**2 < radius**2) * numpy.exp(1. / (x_mesh**2 + y_mesh**2 - radius))

    k = (x_mesh**2 + y_mesh**2 < radius**2) * (radius**2 - x_mesh**2 - y_mesh**2)
    C = numpy.trapz(numpy.trapz(k, x), y)
    return k / C
    
# Kernel mathcal_K (eq. for pirates)
def mathcal_K(x, y):
    radius = .5
    return std_moll(x, y, radius)


# cut-off C (function)
def cut_off_C(x, y, radius = .4):
    # x and y are meshes!
    
    k = (x**2 + y**2 < radius**2) * (radius**2 - x**2 - y**2)
    C = numpy.sum(k) * (x[0][1] - x[0][0]) * (y[1][0] - y[0][0])

    if C < 0.3:
        return k

    return k/C



