#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import base64
import os
import httpx

from ruamel import yaml
from urllib import parse


class SConf:
    ABS_PATH = os.path.dirname(__file__)
    STR_PATTERN = "ss://{pass_encode}@{server}:{port}/?#{name}"

    def __init__(self, uids: list, provider: str) -> None:
        self.url = provider
        self.uids = uids
        self.servers = []
        self.headers = {"helps": "your-agent-here"}
        self.load_default()

    def load_default(self) -> None:
        default_server = f"{self.ABS_PATH}/default-server.yaml"
        if not os.path.exists(default_server):
            return
        with open(default_server, 'r') as fr:
            df = yaml.load(fr, Loader=yaml.Loader)
            if not df.get("servers"):
                return
        self.servers += df.get("servers")

    def collect(self, content: str) -> None:
        servers =  yaml.load(content, Loader=yaml.Loader)
        self.servers += servers.get("proxies")

    async def client(
        self, 
        url: str,
        method: str = "GET",
        headers: dict = {},
        params: dict = {}, 
        expect: int = 200
    ) -> str:
        headers = headers or self.headers
        async with httpx.AsyncClient() as client:
            response = await client.request(
                url=url, 
                method=method, 
                headers=headers, 
                params=params
            )
            if response.status_code not in [expect]:
                return ""
            return response.text

    @property
    async def server(self) -> list:
        for uid in self.uids:
            sub_content = await self.client(
                url=self.url,
                params={"uid": uid},
                expect=200
            )
            if not sub_content:
                continue
            self.collect(content=sub_content)
        return self.servers

    @staticmethod
    async def __ss_row(server: dict) -> str:
        if server.get("type") != "ss":
            return ""
        disp_pattern = "ss://{pass_encode}@{server}:{port}/?#{p_name}"
        try:
            server.update({
                "p_name": parse.quote(server["name"]),
                "pass_encode": base64.b64encode(
                    f"{server['cipher']}:{server['port']}".encode()
                ).decode()
            })
            return disp_pattern.format(**server)
        except KeyError:
            return ""
        
    async def display(self) -> None:
        for server in await self.server:
            row = await self.__ss_row(server=server)
            if row:
                print(row)


if __name__ == "__main__":
    arg = argparse.ArgumentParser()
    arg.add_argument("-u", "--uids", dest="uids", required=True, help="Uids")
    arg.add_argument("-p", "--provider", dest="provider", required=True, help="Subscribe url")
    args = arg.parse_args()

    sc = SConf(
        uids=args.uids.split(","),
        provider=args.provider
    )
    asyncio.run(sc.display())
