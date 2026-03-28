"""
Class definitions package.
Re-exports CLASSES dict for backward compatibility.
"""

from data.classes.scholar import SCHOLAR
from data.classes.brute import BRUTE
from data.classes.warden import WARDEN
from data.classes.shadowblade import SHADOWBLADE
from data.classes.mad_prophet import MAD_PROPHET

CLASSES = {
    "scholar": SCHOLAR,
    "brute": BRUTE,
    "warden": WARDEN,
    "shadowblade": SHADOWBLADE,
    "mad_prophet": MAD_PROPHET,
}
