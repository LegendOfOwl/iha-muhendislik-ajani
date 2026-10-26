"""Explicit SI/ND restart conversion for this 2-D ideal-gas SA benchmark only."""
import struct
import numpy as np


def scales(free):
    rho, speed = free['rho_kg_m3'], free['U_m_s'] / .2
    # SU2 sets length reference to1m for this compressible normalization.
    return {'density': rho, 'velocity': speed, 'length': 1.,
            'solution': np.array([1., 1., rho, rho * speed, rho * speed, rho * speed**2, speed]),
            'residual': {'rms[Rho]': rho * speed, 'rms[RhoU]': rho * speed**2,
                         'rms[RhoV]': rho * speed**2, 'rms[RhoE]': rho * speed**3, 'rms[nu]': speed**2}}


def decode(raw):
    header = struct.unpack('<5i', raw[:20])
    assert header[0] == 535532 and header[1] == 7
    labels = raw[20:20 + 33 * header[1]]
    names = [labels[33 * j:33 * (j + 1)].split(b'\0')[0].decode() for j in range(header[1])]
    assert names == ['x', 'y', 'Density', 'Momentum_x', 'Momentum_y', 'Energy', 'Nu_Tilde']
    data = np.frombuffer(raw, offset=20 + len(labels), dtype='<f8').reshape(header[2], 7).copy()
    assert np.isfinite(data).all()
    return header, labels, data


def primitive(data):
    rho = data[:, 2]
    velocity = data[:, 3:5] / rho[:, None]
    pressure = .4 * (data[:, 5] - .5 * (data[:, 3:5]**2).sum(axis=1) / rho)
    assert (rho > 0).all() and (pressure > 0).all()
    return rho, velocity, pressure


def convert(raw, free):
    header, labels, data = decode(raw)
    scaling = scales(free)
    target = data / scaling['solution']
    restored = target * scaling['solution']
    assert np.array_equal(target[:, :2], data[:, :2])
    old, new = primitive(data), primitive(restored)
    errors = {name: float(np.max(abs(a - b)) / max(np.max(abs(a)), 1e-30))
              for name, a, b in zip(['density', 'velocity', 'pressure'], old, new)}
    assert max(errors.values()) < 3e-15
    nd_primitive = primitive(target)
    # Independent conservative-variable scaling identities.
    assert np.allclose(nd_primitive[0], old[0] / scaling['density'], rtol=3e-15, atol=0)
    assert np.allclose(nd_primitive[1], old[1] / scaling['velocity'], rtol=3e-15, atol=1e-18)
    assert np.allclose(nd_primitive[2], old[2] / (scaling['density'] * scaling['velocity']**2), rtol=3e-15, atol=0)
    output = struct.pack('<5i', *header) + labels + target.astype('<f8').tobytes()
    assert np.array_equal(decode(output)[2], target)
    return output, {'nodes': len(data), 'source_coordinates_bitwise_preserved': True,
                    'SI_roundtrip_relative_errors': errors, 'positive_density_and_pressure': True,
                    'solution_divisors': scaling['solution'].tolist(),
                    'residual_multipliers_2D_integrated_flux': scaling['residual'],
                    'density_reference': scaling['density'], 'velocity_reference_m_s': scaling['velocity'],
                    'limits': 'Specific7-field native binary layout; length reference1m; no general restart conversion.'}


def dimensional_matched(seal, free):
    import copy
    result = copy.deepcopy(seal)
    if result.get('matched'):
        for key, factor in scales(free)['residual'].items():
            if key in result['matched']: result['matched'][key] += float(np.log10(factor))
    result['postprocessing_note'] = 'Residual logs converted from ND to the original SI integrated-flux normalization; force coefficients unchanged.'
    return result
