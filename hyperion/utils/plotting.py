
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from six.moves import xrange

import numpy as np
import scipy.linalg as la

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from mpl_toolkits.mplot3d import Axes3D as plt3d

from .math import invert_pdmat


def plot_gaussian_1D(mu, C, nb_sigmas=3, nb_pts=100, **kwargs):
    sigma = np.sqrt(C)
    delta = nb_sigmas*sigma
    x = np.linspace(mu-delta, mu+delta, nb_pts)
    plt.plot(x, mlab.normpdf(x, mu, sigma), **kwargs)

    
def plot_gaussian_3D(mu, C, nb_sigmas=3, nb_pts=100, ax=None, **kwargs):
    assert(mu.shape[0] == 2)
    assert(C.shape[0] == 2 and C.shape[1] == 2)
    nb_pts *= 1j
    invC, _, logC, _ = invert_pdmat(C, compute_logdet=True)
    dim = mu.shape[0]
    d, v = la.eigh(C)
    delta = nb_sigmas*np.sum(v*np.sqrt(d), axis=1)
    low_lim = mu-delta
    high_lim = mu+delta
    X, Y = np.mgrid[low_lim[0]:high_lim[0]:nb_pts, low_lim[1]:high_lim[1]:nb_pts]
    xy = np.vstack((X.ravel(), Y.ravel()))-mu[:, None]
    z = np.exp(-0.5*dim*np.log(2*np.pi)-0.5*logC-0.5*np.sum(xy*invC(xy), axis=0))

    Z = np.reshape(z, X.shape)
    ax.plot_surface(X, Y, Z, **kwargs)
    

def plot_gaussian_ellipsoid_2D(mu, C, nb_sigmas=1, nb_pts=100, **kwargs):
    assert(mu.shape[0] == 2)
    assert(C.shape[0] == 2 and C.shape[1] == 2)

    t = np.linspace(0,2*np.pi,nb_pts)
    x = np.cos(t)
    y = np.sin(t)
    xy = np.vstack((x,y))
    d, v  =  la.eigh(C)
    d *= nb_sigmas
    r = np.dot(v*d, xy)+mu[:, None]
    plt.plot(r[0,:], r[1,:], **kwargs)

    
def plot_gaussian_ellipsoid_3D(mu, C, nb_sigmas=1, nb_pts=100, ax=None, **kwargs):
    assert(mu.shape[0] == 3)
    assert(C.shape[0] == 3 and C.shape[1] == 3)

    nb_pts *= 1j
    u, v = np.mgrid[0:2*np.pi:nb_pts, 0:np.pi:nb_pts/2]
    x = np.cos(u)*np.sin(v)
    y = np.sin(u)*np.sin(v)
    z = np.cos(v)
    d, v = la.eigh(C)
    xyz = np.vstack((x.ravel(), y.ravel(), z.ravel()))
    r = np.dot(v*d, xyz)+mu[:, None]
    
    X = np.reshape(r[0,:], u.shape)
    Y = np.reshape(r[1,:], u.shape)
    Z = np.reshape(r[2,:], u.shape)
    ax.plot_wireframe(X, Y, Z, **kwargs)


def test_plotting():
    
    mu=np.array([1, 2, 3])
    C=np.array([[2, 0.5, 0.2], [0.5, 1., 0.1], [0.2, 0.1, 0.8]])
    la.cholesky(C)

    mu1 = mu[0]
    C1 = C[0,0]
    plt.figure(figsize=(6, 6))
    plot_gaussian_1D(mu1, C1)
    plt.show()
    plt.savefig('plot_gaussian_1D.pdf')

    mu2 = mu[:2]
    C2 = C[:2,:2]
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    plot_gaussian_3D(mu2, C2, ax=ax)
    plt.show()
    plt.savefig('plot_gaussian_3D.pdf')

    plt.figure(figsize=(6, 6))
    plot_gaussian_ellipsoid_2D(mu2, C2)
    plt.show()
    plt.savefig('plot_gaussian_ellipsoid_2D.pdf')

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    plot_gaussian_ellipsoid_3D(mu, C, ax=ax)
    plt.show()
    plt.savefig('plot_gaussian_ellipsoid_3D.pdf')

    