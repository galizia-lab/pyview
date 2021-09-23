import datetime
import tempfile


def class_mixer(*args):

    class class3(*args):

        def __init__(self, **kwargs):

            super().__init__(**kwargs)

    return class3


# Copyright (c) 2008-2019, Christoph Gohlke
# Copyright (c) 2008-2019, The Regents of the University of California
# Produced at the Laboratory for Fluorescence Dynamics
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
def excel_datetime(timestamp, epoch=None):
    """Return datetime object from timestamp in Excel serial format.

    Convert LSM time stamps.

    >>> excel_datetime(40237.029999999795)
    datetime.datetime(2010, 2, 28, 0, 43, 11, 999982)

    """
    if epoch is None:
        epoch = datetime.datetime.fromordinal(693594)
    return epoch + datetime.timedelta(timestamp)


def interpret_string_as_boolean(str_value):
    """
    Tries to interpret string a boolean. Raises a Value error upon failure.
    """
    if str_value in ("TRUE", "True", "true", "1"):
        return True
    elif str_value in ("False", "FALSE", "false", "0"):
        return False
    else:
        raise ValueError(f"Could not interpret '{str_value}' as a boolean. Valid values are: "
                         f"TRUE, True, true, 1, FALSE, False, false, 0")


def get_system_temp_dir():

    if tempfile.tempdir is None:
        return tempfile.gettempdir()

    else:
        current_tempdir = tempfile.tempdir
        tempfile.tempdir = None
        system_tempdir = tempfile.gettempdir()
        tempfile.tempdir = current_tempdir
        return system_tempdir


