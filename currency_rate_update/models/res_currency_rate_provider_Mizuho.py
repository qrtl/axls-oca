# Copyright 2022 Axelspace
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import xml.sax
import pandas as pd
from collections import defaultdict
from datetime import date, datetime, time
from io import StringIO
import requests
import xml.etree.ElementTree as et

from odoo import fields, models


class ResCurrencyRateProviderMizuho(models.Model):

    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("Mizuho", "Mizuho Bank (Japan)")],
        ondelete={"Mizuho": "set default"},
    )

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "Mizuho":
            return super()._get_supported_currencies()  # pragma: no cover

        # List of currencies obrained from:
        # https://www.mizuhobank.co.jp/market/historical.html
        return [
            "USD",
            "GBP",
            "EUR",
            "CAD",
            "CHF",
            "SEK",
            "DKK",
            "NOK",
            "AUD",
            "NZD",
            "ZAR",
            "BHD",
            "CNY",
            "HKD",
            "INR",
            "MYR",
            "PHP",
            "SGD",
            "THB",
            "KWD",
            "SAR",
            "AED",
            "MXN",
            "PGK",
            "HUF",
            "CZK",
            "PLN",
            "TRY",
        ]

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "Mizuho":
            return super()._obtain_rates(
                base_currency, currencies, date_from, date_to
            )  # pragma: no cover
        invert_calculation = False
        if base_currency != "JPY":
            invert_calculation = True
            if base_currency not in currencies:
                currencies.append(base_currency)

        # Depending on the date range, different URLs are used
        url = "https://www.mizuhobank.co.jp/market/csv"
        if self._Is_in_this_month(date_from, date_to):
            url = url + "/tm_quote.csv"
        else:
            url = url + "/quote.csv"

        handler = RatesHandler(currencies, date_from, date_to)
        xml.sax.parseString(self._get_mizuho_rates(url, date_from), handler)
        content = handler.content
        if invert_calculation:
            for k in content.keys():
                base_rate = float(content[k][base_currency])
                for rate in content[k].keys():
                    content[k][rate] = str(float(content[k][rate]) / base_rate)
                content[k]["JPY"] = str(1.0 / base_rate)
        return content

    def _get_mizuho_rates(self, url: str, date_from: date) -> str:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
        response = requests.get(url=url, headers=headers)
        response.encoding = response.apparent_encoding
        # Read CSV and adjustment
        df = pd.read_csv(StringIO(response.text), header=2)
        df = df.rename(columns={"Unnamed: 0": "Date"})
        df = df.dropna(axis=1, how='all')
        df["Date"] = df["Date"].str.replace("/", "-")  # Convert date format to iso format
        df["Date"] = pd.to_datetime(df["Date"])
        df = df[df["Date"] > datetime.combine(date_from, time())]    # delete before date_from
        # convert df to XML
        root = et.Element("root")
        elm1 = et.Element("Cube")
        root.append(elm1)
        for i, row in df.iterrows():
            sub_eml = et.SubElement(elm1, "Cube", attrib={"time": str(row[0])})
            for j, colName in enumerate(df.columns.values):
                if colName == "Date":
                    continue
                if str(row[j]) == "*****":
                    continue
                et.SubElement(sub_eml, "Cube", attrib={"currency": colName, "rate": str(row[j])})
        return et.tostring(root)

    def _Is_in_this_month(self, date_from: date, date_to: date):
        d_today = date.today()
        ym_from = date_from.year + date_from.month
        ym_to = date_to.year + date_to.month
        ym_now = d_today.year + d_today.month
        if (ym_from == ym_to == ym_now):
            return True
        else:
            return False


class RatesHandler(xml.sax.ContentHandler):
    def __init__(self, currencies, date_from, date_to):
        self.currencies = currencies
        self.date_from = date_from
        self.date_to = date_to
        self.date = None
        self.content = defaultdict(dict)

    def startElement(self, name, attrs):
        if name == "Cube" and "time" in attrs:
            self.date = fields.Date.from_string(attrs["time"])
        elif name == "Cube" and all([x in attrs for x in ["currency", "rate"]]):
            currency = attrs["currency"]
            rate = attrs["rate"]
            if (
                (self.date_from is None or self.date >= self.date_from)
                and (self.date_to is None or self.date <= self.date_to)
                and currency in self.currencies
            ):
                self.content[self.date.isoformat()][currency] = rate
