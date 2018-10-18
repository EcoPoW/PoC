"""
Copyright (C) 2018 NuCypher

This file is part of pyUmbral.

pyUmbral is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pyUmbral is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pyUmbral. If not, see <https://www.gnu.org/licenses/>.
"""

from typing import Optional

from umbral.curvebn import CurveBN
from umbral.keys import UmbralPublicKey


def prove_cfrag_correctness(cfrag: 'CapsuleFrag',
                            kfrag: 'KFrag',
                            capsule: 'Capsule',
                            metadata: Optional[bytes] = None
                            ) -> 'CorrectnessProof':

    params = capsule._umbral_params

    rk = kfrag._bn_key
    t = CurveBN.gen_rand(params.curve)
    ####
    # Here are the formulaic constituents shared with `assess_cfrag_correctness`.
    ####
    e = capsule._point_e
    v = capsule._point_v

    e1 = cfrag._point_e1
    v1 = cfrag._point_v1

    u = params.u
    u1 = kfrag._point_commitment

    e2 = t * e
    v2 = t * v
    u2 = t * u

    hash_input = (e, e1, e2, v, v1, v2, u, u1, u2)
    if metadata is not None:
        hash_input += (metadata,)
    h = CurveBN.hash(*hash_input, params=params)
    ########

    z3 = t + h * rk

    cfrag.attach_proof(e2, v2, u1, u2, metadata=metadata, z3=z3, kfrag_signature=kfrag.signature)

    # Check correctness of original ciphertext (check nº 2) at the end
    # to avoid timing oracles
    if not capsule.verify():
        raise capsule.NotValid("Capsule verification failed.")


def assess_cfrag_correctness(cfrag: 'CapsuleFrag', capsule: 'Capsule') -> bool:

    correctness_keys = capsule.get_correctness_keys()

    delegating_pubkey = correctness_keys['delegating']
    signing_pubkey = correctness_keys['verifying']
    receiving_pubkey = correctness_keys['receiving']

    if not all((delegating_pubkey, signing_pubkey, receiving_pubkey)):
        raise TypeError("Need all three keys to verify correctness.")

    delegating_point = delegating_pubkey.point_key
    receiving_point = receiving_pubkey.point_key

    params = capsule._umbral_params

    ####
    # Here are the formulaic constituents shared with `prove_cfrag_correctness`.
    ####
    e = capsule._point_e
    v = capsule._point_v

    e1 = cfrag._point_e1
    v1 = cfrag._point_v1

    u = params.u
    try:
        u1 = cfrag.proof._point_kfrag_commitment

        e2 = cfrag.proof._point_e2
        v2 = cfrag.proof._point_v2
        u2 = cfrag.proof._point_kfrag_pok
    except AttributeError:
        if cfrag.proof is None:
            raise cfrag.NoProofProvided
        else:
            raise

    hash_input = (e, e1, e2, v, v1, v2, u, u1, u2)
    if cfrag.proof.metadata is not None:
        hash_input += (cfrag.proof.metadata,)
    h = CurveBN.hash(*hash_input, params=params)
    ########

    ni = cfrag._point_noninteractive
    xcoord = cfrag._point_xcoord
    kfrag_id = cfrag._kfrag_id

    kfrag_validity_message = bytes().join(
        bytes(material) for material in (kfrag_id, delegating_point, receiving_point, u1, ni, xcoord))
    valid_kfrag_signature = cfrag.proof.kfrag_signature.verify(kfrag_validity_message, signing_pubkey)

    z3 = cfrag.proof.bn_sig
    correct_reencryption_of_e = z3 * e == e2 + (h * e1)

    correct_reencryption_of_v = z3 * v == v2 + (h * v1)

    correct_rk_commitment = z3 * u == u2 + (h * u1)

    return valid_kfrag_signature \
           & correct_reencryption_of_e \
           & correct_reencryption_of_v \
           & correct_rk_commitment


def verify_kfrag(kfrag: 'KFrag',
                 delegating_pubkey: UmbralPublicKey,
                 signing_pubkey: UmbralPublicKey,
                 receiving_pubkey: UmbralPublicKey
                 ) -> bool:


    params = delegating_pubkey.params
    if not params == receiving_pubkey.params:
        raise ValueError("The delegating and receiving keys must use the same UmbralParameters")

    u = params.u

    delegating_point = delegating_pubkey.point_key
    receiving_point = receiving_pubkey.point_key

    id = kfrag._id
    key = kfrag._bn_key
    u1 = kfrag._point_commitment
    ni = kfrag._point_noninteractive
    xcoord = kfrag._point_xcoord

    #  We check that the commitment u1 is well-formed
    correct_commitment = u1 == key * u

    kfrag_validity_message = bytes().join(
        bytes(material) for material in (id, delegating_point, receiving_point, u1, ni, xcoord))
    valid_kfrag_signature = kfrag.signature.verify(kfrag_validity_message, signing_pubkey)

    return correct_commitment & valid_kfrag_signature
