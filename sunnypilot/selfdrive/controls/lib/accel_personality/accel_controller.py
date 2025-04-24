"""
Copyright (c) 2021-, rav4kumar, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from cereal import custom
from numpy import interp
from openpilot.common.realtime import DT_MDL
from openpilot.common.params import Params

from openpilot.sunnypilot.selfdrive.controls.lib.accel_personality.accel_profiles import (
  MAX_ACCEL_ECO, MAX_ACCEL_NORMAL, MAX_ACCEL_SPORT,
  MAX_ACCEL_BREAKPOINTS, MIN_ACCEL_BREAKPOINTS,
  get_min_accel_spline
)


AccelPersonality = custom.LongitudinalPlanSP.AccelerationPersonality

def clamp(val: float, lower: float, upper: float) -> float:
  return max(lower, min(val, upper))

class AccelController:
  def __init__(self):
    self.params = Params()
    self.personality = AccelPersonality.stock
    self.frame = 0

  def _update_personality_from_param(self):
    if self.frame % int(1. / DT_MDL) == 0:
      personality_str = self.params.get("AccelPersonality", encoding='utf-8')
      if personality_str is not None:
        personality_int = int(personality_str)
        if personality_int in [AccelPersonality.stock, AccelPersonality.normal, AccelPersonality.eco, AccelPersonality.sport]:
          self.personality = personality_int

  def _get_max_accel_for_speed(self, v_ego: float) -> float:
    self._update_personality_from_param()

    # Clamp v_ego to valid interpolation range
    v_ego = clamp(v_ego, MAX_ACCEL_BREAKPOINTS[0], MAX_ACCEL_BREAKPOINTS[-1])

    if self.personality == AccelPersonality.eco:
      accel_profile = MAX_ACCEL_ECO
    elif self.personality == AccelPersonality.sport:
      accel_profile = MAX_ACCEL_SPORT
    else:
      accel_profile = MAX_ACCEL_NORMAL

    return float(interp(v_ego, MAX_ACCEL_BREAKPOINTS, accel_profile))

  def _get_min_accel_for_speed(self, v_ego: float) -> float:
    self._update_personality_from_param()

    if self.personality == AccelPersonality.eco:
      mode = "eco"
    elif self.personality == AccelPersonality.sport:
      mode = "sport"
    elif self.personality == AccelPersonality.normal:
      mode = "normal"
    else:
      mode = "stock"

    return get_min_accel_spline(v_ego, mode)

  def get_accel_limits(self, v_ego: float, accel_limits: list[float]) -> tuple[float, float]:
    self._update_personality_from_param()

    if self.personality == AccelPersonality.stock:
      return (accel_limits[0], accel_limits[1])
    else:
      max_accel = self._get_max_accel_for_speed(v_ego)
      return (accel_limits[0], max_accel)

  def is_personality_enabled(self, accel_personality: int = AccelPersonality.stock) -> bool:
    self.personality = accel_personality
    self._update_personality_from_param()
    return bool(self.personality != AccelPersonality.stock)

  def update(self):
    self.frame += 1
