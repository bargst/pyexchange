# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import asyncio
from pprint import pformat
from typing import List

import requests

from pymaker.numeric import Wad
from pymaker.util import http_response_summary


class Trade:
    def __init__(self,
                 trade_id: id,
                 timestamp: float,
                 price: Wad,
                 amount: Wad):
        assert(isinstance(trade_id, int))
        assert(isinstance(timestamp, float))
        assert(isinstance(price, Wad))
        assert(isinstance(amount, Wad))

        self.trade_id = trade_id
        self.timestamp = timestamp
        self.price = price
        self.amount = amount

    def __eq__(self, other):
        assert(isinstance(other, Trade))
        return self.trade_id == other.trade_id and \
               self.timestamp == other.timestamp and \
               self.price == other.price and \
               self.amount == other.amount

    def __hash__(self):
        return hash((self.trade_id,
                     self.timestamp,
                     self.price,
                     self.amount))

    def __repr__(self):
        return pformat(vars(self))


class BinanceApi:
    """Binance API interface.

    Developed according to the following manual:
    <https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md>.
    """

    logger = logging.getLogger()

    def __init__(self, api_server: str, timeout: float):
        assert(isinstance(api_server, str))
        assert(isinstance(timeout, float))

        self.api_server = api_server
        self.timeout = timeout
        self.loop = asyncio.get_event_loop()

    def get_all_trades(self, pair: str) -> List[Trade]:
        assert(isinstance(pair, str))

        result = self._http_get("/api/v1/trades", f"symbol={pair}")
        return list(map(lambda item: Trade(trade_id=int(item['id']),
                                           timestamp=float(item['time']/1000),
                                           price=Wad.from_number(item['price']),
                                           amount=Wad.from_number(item['qty'])), result))

    async def async_get_all_trades(self, pair: str) -> List[Trade]:
        assert(isinstance(pair, str))

        result = await self.loop.run_in_executor(None, self._http_get, "/api/v1/trades", f"symbol={pair}")
        return list(map(lambda item: Trade(trade_id=int(item['id']),
                                           timestamp=float(item['time']/1000),
                                           price=Wad.from_number(item['price']),
                                           amount=Wad.from_number(item['qty'])), result))

    @staticmethod
    def _result(result) -> dict:
        if not result.ok:
            raise Exception(f"Binance API invalid HTTP response: {http_response_summary(result)}")

        try:
            data = result.json()
        except Exception:
            raise Exception(f"Binance API invalid JSON response: {http_response_summary(result)}")

        return data

    def _http_get(self, resource: str, params: str):
        assert(isinstance(resource, str))
        assert(isinstance(params, str))

        return self._result(requests.get(url=f"{self.api_server}{resource}?{params}",
                                         timeout=self.timeout))
