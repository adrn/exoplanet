# -*- coding: utf-8 -*-

from __future__ import division, print_function

import numpy as np

from batman import _rsky

import theano
import theano.tensor as tt
from theano.tests import unittest_tools as utt

from .keplerian import KeplerianOrbit


def test_sky_coords():
    t = np.linspace(-100, 100, 1000)

    t0, period, a, e, omega, incl = (x.flatten() for x in np.meshgrid(
        np.linspace(-5.0, 5.0, 2),
        np.exp(np.linspace(np.log(5.0), np.log(50.0), 3)),
        np.linspace(50.0, 100.0, 2),
        np.linspace(0.0, 0.9, 5),
        np.linspace(-np.pi, np.pi, 3),
        np.arccos(np.linspace(0, 1, 5)[:-1]),
    ))
    r_batman = np.empty((len(t), len(t0)))

    for i in range(len(t0)):
        r_batman[:, i] = _rsky._rsky(t, t0[i], period[i], a[i], incl[i], e[i],
                                     omega[i], 1, 1)
    m = r_batman < 100.0

    orbit = KeplerianOrbit(
        period=period, a=a, t0=t0, ecc=e, omega=omega, incl=incl, tol=1e-7)
    func = theano.function([], orbit.get_relative_position(t))
    x, y, z = func()
    r = np.sqrt(x**2 + y**2)

    # Make sure that the in-transit impact parameter matches batman
    utt.assert_allclose(r_batman[m], r[m], atol=2e-5)

    # In-transit should correspond to negative z in our parameterization
    assert np.all(z[m] < 0)

    # Therefore, when batman doesn't see a transit we shouldn't be transiting
    no_transit = z[~m] > 0
    no_transit |= r[~m] > 1
    assert np.all(no_transit)


def test_center_of_mass():
    t = np.linspace(0, 100, 1000)
    m_planet = np.array([0.5, 0.1])
    m_star = 1.45
    orbit = KeplerianOrbit(
        m_star=m_star,
        r_star=1.0,
        t0=np.array([0.5, 17.4]),
        period=np.array([100.0, 37.3]),
        ecc=np.array([0.1, 0.8]),
        omega=np.array([0.5, 1.3]),
        incl=np.array([0.25*np.pi, 0.3*np.pi]),
        m_planet=m_planet,
    )

    planet_coords = theano.function([], orbit.get_planet_position(t))()
    star_coords = theano.function([], orbit.get_star_position(t))()

    com = np.sum((m_planet[None, :] * np.array(planet_coords) +
                  m_star * np.array(star_coords)) /
                 (m_star + m_planet)[None, :], axis=0)
    assert np.allclose(com, 0.0)


def test_velocity():
    t_tensor = tt.dvector()
    t = np.linspace(0, 100, 1000)
    m_planet = 0.1
    m_star = 1.3
    orbit = KeplerianOrbit(
        m_star=m_star,
        r_star=1.0,
        t0=0.5,
        period=100.0,
        ecc=0.1,
        omega=0.5,
        incl=0.25*np.pi,
        m_planet=m_planet,
    )

    star_pos = orbit.get_star_position(t_tensor)
    star_vel = theano.function([], orbit.get_star_velocity(t))()
    star_vel_expect = np.empty_like(star_vel)
    for i in range(3):
        g = theano.grad(tt.sum(star_pos[i]), t_tensor)
        star_vel_expect[i] = theano.function([t_tensor], g)(t)
    utt.assert_allclose(star_vel, star_vel_expect)

    planet_pos = orbit.get_planet_position(t_tensor)
    planet_vel = theano.function([], orbit.get_planet_velocity(t))()
    planet_vel_expect = np.empty_like(planet_vel)
    for i in range(3):
        g = theano.grad(tt.sum(planet_pos[i]), t_tensor)
        planet_vel_expect[i] = theano.function([t_tensor], g)(t)
    utt.assert_allclose(planet_vel, planet_vel_expect)