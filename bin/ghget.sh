#!/bin/sh

#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-
# bin/ghget.sh -o suiprot https://github.com/MystenLabs/sui/tree/main/crates/sui-rpc-api/proto

set -euo pipefail

name=$(basename "$0")

usage() {
	printf "usage: %s [-o path] url\n" "$name" >&2
	exit 2
}

out=

while getopts :o: opt; do
	case $opt in
	o) out=$OPTARG; if [ -z "$out" ]; then usage; fi ;;
	?) usage
	esac
done
shift $((OPTIND-1))

if [ "$#" -ne 1 ]; then
	usage
fi

ver() {
	printf "%s\n" "$1" | awk -F. '{ print $1*1e6 + $2*1e3 + $3 }'
}

curl=$(curl -V | awk 'NR == 1 { print $2 }')
parallel=
if [ "$(ver "$curl")" -ge "$(ver 7.66.0)" ]; then
	parallel=-Z
fi

LC_ALL=C awk -v apos="'" '
function decode_url(url, rest) {
	rest = url
	url = ""
	while (match(rest, /%[0-9a-fA-F][0-9a-fA-F]/)) {
		url = url substr(rest, 1, RSTART - 1) \
			urldec[substr(rest, RSTART, RLENGTH)]
		rest = substr(rest, RSTART + RLENGTH)
	}
	return url rest
}
function encode_url_part(s, res, i, c) {
	res = ""
	for (i = 1; i <= length(s); i++) {
		c = substr(s, i, 1);
		res = res (c ~ /[0-9A-Za-z._-]/ ? c : sprintf("%%%02X", ord[c]))
	}
	return res
}
function escape_shell_arg(arg) {
	gsub(apos, apos "\\" apos apos, arg)
	return apos arg apos
}
function decode_json_string(s) {
	if (s !~ /^"/) error("invalid json string " s)
	s = substr(s, 2, length(s)-2)
	gsub(/\\"/, "\"", s)
	gsub(/\\\\/, "\\", s)
	return s
}
function get_json_value( \
	s, key, \
	type, all, rest, isval, i, c, j, k \
) {
	type = substr(s, 1, 1)
	if (type != "{" && type != "[") error("invalid json array/object " s)
	all = key == "" && key == 0
	if (!all && (j = index(key, "."))) {
		rest = substr(key, j+1)
		key = substr(key, 1, j-1)
	}
	if (type == "[") k = 0
	isval = type == "["
	for (i = 2; i < length(s); i += length(c)) {
		c = substr(s, i, 1)
		if (c == "\"") {
			if (!match(substr(s, i), /^"(\\.|[^\\"])*"/))
				error("invalid json string " substr(s, i))
			c = substr(s, i, RLENGTH)
			if (!isval) k = substr(c, 2, length(c)-2)
		}
		else if (c == "{" || c == "[") {
			c = (!all && k == key && !(rest == "" && rest == 0)) ? \
				get_json_value(substr(s, i), rest) : \
				get_json_value(substr(s, i))
		}
		else if (c == "}" || c == "]") break
		else if (c == ",") isval = type == "["
		else if (c == ":") ;
		else if (c ~ /[[:space:]]/) continue
		else {
			if (!match(substr(s, i), /[]},[:space:]]/))
				error("invalid json value " substr(s, i))
			c = substr(s, i, RSTART-1)
		}
		if (!all && isval && k == key) return c
		if (type == "{" && c == ":") isval = 1
		if (type == "[" && c == ",") ++k
	}
	if (all) return substr(s, 1, i)
}
function get_path(url, parts, n, path, i) {
	n = split(url, parts, "/")
	path = ""
	for (i=4; i<=n; i++) if (i != 6) path = path "/" parts[i]
	return path
}
function get_type(url, parts) {
	split(url, parts, "/")
	return parts[6]
}
function get_raw_url(path) {
	return "https://raw.githubusercontent.com" path
}
function get_file(path, output, root) {
	path = substr(path, length(root)+2)
	return path ? output "/" decode_url(path) : output
}
function error(msg) {
	printf "%s: %s\n", ARGV[0], msg > "/dev/stderr"
	exit 1
}
function debug(msg) {
	printf "%s: %s\n", ARGV[0], msg > "/dev/stderr"
}
function print_links( \
	url, output, root, \
	type, path, file, cmd, s, l, ret, items, i, item, name, parts, n, j \
) {
	if (!output) {
		match(url, /\/[^\/]+$/)
		output = decode_url(substr(url, RSTART+1))
	}
	if (split(url, parts, "/") < 6) url = url "/tree/HEAD"
	type = get_type(url)
	path = get_path(url)
	if (!root) root = path
	if (type == "blob") {
		++total
		file = get_file(path, output, root)
		url = get_raw_url(path)
		gsub(/"/, "\"\\\"\"", file)
		gsub(/"/, "\"\\\"\"", url)
		printf "%s:\t\t\t %d files\r", ARGV[0], total > "/dev/stderr"
		printf "-o \"%s\" --url \"%s\" " \
			"-w \"%%{stderr}\t\bdownloaded %4d /\\r\"\n", \
			file, url, total
		return
	}
	cmd = "curl -fsSLH Accept:application/json -- " escape_shell_arg(url)
	s = ""
	while (ret = cmd | getline l) {
		if (ret == -1) error("getline error")
		s = s l
	}
	close(cmd)
	if (!s || !(items = get_json_value(s, "payload.tree.items")))
		error("failed to get file list")
	while ((item = get_json_value(items, i++))) {
		type = decode_json_string(get_json_value(item, "contentType"))
		name = decode_json_string(get_json_value(item, "name"))
		if (type == "file") {
			n = split(url, parts, "/")
			url = parts[1]
			for (j=2; j<=n; j++) url = url "/" (j == 6 ? "blob" : parts[j])
		}
		print_links(url "/" encode_url_part(name), output, root)
	}
}
BEGIN {
	for (i = 0; i < 256; i++) {
		c = sprintf("%c", i)
		ord[c] = i
		urldec[sprintf("%%%02X", i)] = c
		urldec[sprintf("%%%02x", i)] = c
	}
	for (i=0; i<ARGC; i++) ARGV[i] = ARGV[i+1]; --ARGC
	sub(/\/$/, "", ARGV[1])
	print_links(ARGV[1], ARGV[2])
}
' "$name" "$1" "$out" |
xargs -E '' -L4 sh -c \
"curl --create-dirs --fail-early $parallel -fsSL \"\$@\" || exit 255" "$0"
echo >&2
