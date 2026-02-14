import re
from typing import List, Dict, Optional

COIN_PATTERNS = {
    "BTC": ["bitcoin", "btc", "xbt"],
    "ETH": ["ethereum", "eth", "ether"],
    "SOL": ["solana", "sol"],
    "BNB": ["binance coin", "bnb", "binancecoin"],
    "XRP": ["ripple", "xrp"],
    "ADA": ["cardano", "ada"],
    "DOGE": ["dogecoin", "doge"],
    "DOT": ["polkadot", "dot"],
    "AVAX": ["avalanche", "avax"],
    "MATIC": ["polygon", "matic"],
    "LINK": ["chainlink", "link"],
    "UNI": ["uniswap", "uni"],
    "ATOM": ["cosmos", "atom"],
    "LTC": ["litecoin", "ltc"],
    "XLM": ["stellar", "xlm"],
    "ALGO": ["algorand", "algo"],
    "VET": ["vechain", "vet"],
    "FIL": ["filecoin", "fil"],
    "THETA": ["theta", "theta token"],
    "AAVE": ["aave", "lend"],
    "MKR": ["maker", "mkr"],
    "SNX": ["synthetix", "snx"],
    "CRV": ["curve dao", "curve", "crv"],
    "SUSHI": ["sushiswap", "sushi"],
    "COMP": ["compound", "comp"],
    "YFI": ["yearn finance", "yfi", "yearn"],
    "SAND": ["the sandbox", "sandbox", "sand"],
    "MANA": ["decentraland", "mana"],
    "AXS": ["axie infinity", "axs"],
    "ENJ": ["enjin", "enj"],
    "CHZ": ["chiliz", "chz"],
    "BAT": ["basic attention token", "bat"],
    "ZEC": ["zcash", "zec"],
    "DASH": ["dash", "dash coin"],
    "XMR": ["monero", "xmr"],
    "NEAR": ["near protocol", "near"],
    "APT": ["aptos", "apt"],
    "ARB": ["arbitrum", "arb"],
    "OP": ["optimism", "op"],
    "LDO": ["lido dao", "lido", "ldo"],
    "RUNE": ["thorchain", "rune"],
    "KAVA": ["kava", "kava"],
    "FTM": ["fantom", "ftm"],
    "SCRT": ["secret", "scrt"],
    "ONE": ["harmony", "one"],
    "CELO": ["celo", "celo"],
    "QTUM": ["qtum", "qtum"],
    "EGLD": ["elrond", "egld", "multiversx"],
    "FLOW": ["flow", "flow"],
    "HBAR": ["hedera", "hbar", "hashgraph"],
    "XTZ": ["tezos", "xtz"],
    "EOS": ["eos", "eos"],
    "CAKE": ["pancakeswap", "cake"],
    "PEPE": ["pepe", "pepecoin"],
    "SHIB": ["shiba inu", "shib"],
    "TRX": ["tron", "trx"],
    "USDT": ["tether", "usdt"],
    "USDC": ["usd coin", "usdc"],
    "DAI": ["dai", "dai"],
    "BUSD": ["binance usd", "busd"],
    "TUSD": ["trueusd", "tusd"],
}


class CoinDetector:
    def __init__(self):
        self._build_patterns()

    def _build_patterns(self):
        self.patterns = {}
        for symbol, variants in COIN_PATTERNS.items():
            pattern = r"\b(" + "|".join(re.escape(v) for v in variants) + r")\b"
            self.patterns[symbol] = re.compile(pattern, re.IGNORECASE)

    def detect_coins(
        self, title: str = "", summary: str = "", content: str = ""
    ) -> List[Dict]:
        detected = {}
        text = f"{title} {summary} {content}"

        for symbol, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                unique_matches = set(m.lower() for m in matches)
                confidence = min(0.95, 0.3 + (len(unique_matches) * 0.1))

                detected[symbol] = {
                    "symbol": symbol,
                    "confidence": round(confidence, 2),
                    "mentions": len(matches),
                    "mentioned_in": self._get_mentioned_locations(
                        title, summary, content, symbol
                    ),
                }

        return list(detected.values())

    def _get_mentioned_locations(
        self, title: str, summary: str, content: str, symbol: str
    ) -> List[str]:
        locations = []
        pattern = self.patterns.get(symbol, re.compile(r"", re.IGNORECASE))

        if pattern.search(title):
            locations.append("title")
        if pattern.search(summary):
            locations.append("summary")
        if pattern.search(content):
            locations.append("content")

        return locations if locations else ["text"]

    def get_unique_coins(self, coins: List[Dict]) -> List[str]:
        return list(set(c["symbol"] for c in coins))
