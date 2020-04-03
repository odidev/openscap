#!/usr/bin/python3

# Copyright (C) 2020 Matěj Týč <matyc@redhat.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301 USA

import argparse
import datetime
import re
import xml.etree.ElementTree as ET


ALL_NS = {
    "xccdf-1.1": "http://checklists.nist.gov/xccdf/1.1",
    "xccdf-1.2": "http://checklists.nist.gov/xccdf/1.2",
}
DEFAULT_PROFILE_SUFFIX = "_customized"


def id_is_full(string):
    return re.match(r"^xccdf_org\.", string) is not None


class Tailoring:
    PROFILES_PREFIX = "xccdf_org.ssgproject.content_profile_"
    RULES_PREFIX = "xccdf_org.ssgproject.content_rule_"
    VARS_PREFIX = "xccdf_org.ssgproject.content_value_"

    def __init__(self):
        self.id_suffix = "auto_tailoring_default"
        self.version = 1
        self.profile_name = ""
        self.extends = ""
        self.original_ds_filename = ""
        self.profile_title = ""

        self.value_changes = []
        self.rules_to_select = []
        self.rules_to_unselect = []

    def _full_id(self, string, default_prefix):
        if id_is_full(string):
            return string
        return default_prefix + string

    def _full_profile_id(self, string):
        return self._full_id(string, self.PROFILES_PREFIX)

    def _full_var_id(self, string):
        return self._full_id(string, self.VARS_PREFIX)

    def _full_rule_id(self, string):
        return self._full_id(string, self.RULES_PREFIX)

    def add_value_change(self, varname, value):
        self.value_changes.append((varname, value))

    def to_xml(self, location=None):
        root = ET.Element("xccdf-1.2:Tailoring")
        root.set("xmlns:xccdf-1.2", ALL_NS["xccdf-1.2"])
        root.set("id", "xccdf_" + self.id_suffix)

        benchmark = ET.SubElement(root, "xccdf-1.2:benchmark")
        benchmark.set("href", self.original_ds_filename)

        version = ET.SubElement(root, "xccdf-1.2:version")
        version.set("time", datetime.datetime.now().isoformat())
        version.text = str(self.version)

        profile = ET.SubElement(root, "xccdf-1.2:Profile")
        profile.set("id", self._full_profile_id(self.profile_name))
        profile.set("extends", self._full_profile_id(self.extends))

        # Title has to be there due to the schema definition.
        title = ET.SubElement(profile, "xccdf-1.2:title")
        if self.profile_title:
            title.set("override", "true")
        else:
            title.set("override", "false")
        title.text = self.profile_title

        for rule_id in self.rules_to_select:
            change = ET.SubElement(profile, "xccdf-1.2:select")
            change.set("idref", self._full_rule_id(rule_id))
            change.set("selected", "true")

        for rule_id in self.rules_to_unselect:
            change = ET.SubElement(profile, "xccdf-1.2:select")
            change.set("idref", self._full_rule_id(rule_id))
            change.set("selected", "false")

        for varname, value in self.value_changes:
            change = ET.SubElement(profile, "xccdf-1.2:set-value")
            change.set("idref", self._full_var_id(varname))
            change.text = str(value)

        if location:
            ET.ElementTree(root).write(location)
        else:
            try:
                # Python >= 3.9
                ET.indent(root)
            except AttributeError:
                ET.dump(root)


def parse_args():
    parser = argparse.ArgumentParser(
        description="This script produces XCCDF 1.2 tailoring files to be used by SCAP scanners and SCAP datastreams.")
    parser.add_argument(
        "datastream", metavar="DS-FILENAME",
        help="The datastream filename is just informational, "
        "it doesn't have any key role in the tailoring composition.")
    parser.add_argument(
        "profile", metavar="BASE_PROFILE_ID",
        help="Specify ID of the base profile. "
        "ID of the profile can be either its full ID, or the suffix, in which case "
        "the '{prefix}' prefix will be prepended internally."
        .format(prefix=Tailoring.PROFILES_PREFIX))
    parser.add_argument(
        "--title", default="",
        help="Title of the new profile.")
    parser.add_argument(
        "-v", "--var-value", metavar="VAR=VALUE", action="append", default=[],
        help="Specify modification of the XCCDF value in form <varname>=<value>. "
        "Name of the variable can be either its full name, or the suffix, in which case "
        "the '{prefix}' prefix will be prepended internally. "
        "Specify the argument multiple times if needed."
        .format(prefix=Tailoring.VARS_PREFIX))
    parser.add_argument(
        "-s", "--select", metavar="RULE_ID", action="append", default=[],
        help="Specify what rules to select. "
        "The rule ID can be either full, or just the suffix, in which case "
        "the '{prefix}' prefix will be prepended internally. "
        "Specify the argument multiple times if needed."
        .format(prefix=Tailoring.RULES_PREFIX))
    parser.add_argument(
        "-u", "--unselect", metavar="RULE_ID", action="append", default=[],
        help="Specify what rules to unselect. "
        "The argument works the same way as the --select argument.")
    parser.add_argument(
        "-p", "--new-profile-id",
        help="Specify the ID of the tailored profile. "
        "The ID of the new profile can be either its full ID, or the suffix, in which case "
        "the '{prefix}' prefix will be prepended internally. "
        "If left out, the new ID will be obtained "
        "by appending '{suffix}' to the tailored profile ID."
        .format(prefix=Tailoring.PROFILES_PREFIX, suffix=DEFAULT_PROFILE_SUFFIX))
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    return args


def assignment_to_tuple(assignment):
    varname, value = assignment.split("=", 1)
    return (varname, value)


if __name__ == "__main__":
    args = parse_args()
    for prefix, uri in ALL_NS.items():
        ET.register_namespace(prefix, uri)

    t = Tailoring()
    t.extends = args.profile
    if args.new_profile_id:
        t.profile_name = args.new_profile_id
    else:
        t.profile_name = args.profile
    t.original_ds_filename = args.datastream
    for change in args.var_value:
        varname, value = assignment_to_tuple(change)
        t.add_value_change(varname, value)

    t.profile_title = args.title

    t.rules_to_select = args.select
    t.rules_to_unselect = args.unselect

    t.to_xml(args.output)
