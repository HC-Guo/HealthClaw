#!/usr/bin/env python3
"""Manage logical device bindings without manually editing JSON files."""
import argparse
import json
import urllib.request

from cross_device_node import (
    delete_node_binding,
    list_device_bindings,
    upsert_node_binding,
)


def http_get_json(url, timeout=10):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return {
            "status": "success",
            "http_status": resp.status,
            "response": json.loads(raw) if raw else {},
        }


def http_post_json(url, payload, token="", timeout=10):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-OpenClaw-Token"] = token
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return {
            "status": "success",
            "http_status": resp.status,
            "response": json.loads(raw) if raw else {},
        }


def main():
    parser = argparse.ArgumentParser(description="Manage OpenClaw cross-device bindings.")
    parser.add_argument("--binding-file", default="memory/device_bindings.json", help="Binding config path")
    parser.add_argument("--server-url", default="", help="Optional running node base URL, e.g. http://10.0.0.8:8790")
    sub = parser.add_subparsers(dest="command", required=True)

    upsert = sub.add_parser("upsert", help="Create or update one sender->target binding")
    upsert.add_argument("--sender-id", required=True)
    upsert.add_argument("--target-id", required=True)
    upsert.add_argument("--endpoint", required=True)
    upsert.add_argument("--token", default="")
    upsert.add_argument("--sender-role", default="elder")
    upsert.add_argument("--target-role", default="caregiver")
    upsert.add_argument("--sender-name", default="")
    upsert.add_argument("--target-name", default="")
    upsert.add_argument("--recipient-open-id", default="")

    delete = sub.add_parser("delete", help="Delete one sender->target binding")
    delete.add_argument("--sender-id", required=True)
    delete.add_argument("--target-id", required=True)

    sub.add_parser("list", help="Print current binding config")

    args = parser.parse_args()

    if args.command == "upsert":
        if args.server_url:
            data = http_post_json(
                args.server_url.rstrip("/") + "/bindings/upsert",
                {
                    "sender_id": args.sender_id,
                    "target_id": args.target_id,
                    "endpoint": args.endpoint,
                    "token": args.token,
                    "sender_role": args.sender_role,
                    "target_role": args.target_role,
                    "sender_name": args.sender_name,
                    "target_name": args.target_name,
                    "recipient_open_id": args.recipient_open_id,
                },
            )["response"]
        else:
            data = upsert_node_binding(
                sender_id=args.sender_id,
                target_id=args.target_id,
                endpoint=args.endpoint,
                token=args.token,
                sender_role=args.sender_role,
                target_role=args.target_role,
                sender_name=args.sender_name,
                target_name=args.target_name,
                recipient_open_id=args.recipient_open_id,
                path=args.binding_file,
            )
    elif args.command == "delete":
        if args.server_url:
            data = http_post_json(
                args.server_url.rstrip("/") + "/bindings/delete",
                {
                    "sender_id": args.sender_id,
                    "target_id": args.target_id,
                },
            )["response"]
        else:
            data = delete_node_binding(
                sender_id=args.sender_id,
                target_id=args.target_id,
                path=args.binding_file,
            )
    else:
        if args.server_url:
            data = http_get_json(args.server_url.rstrip("/") + "/bindings")["response"]
        else:
            data = list_device_bindings(path=args.binding_file)

    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
