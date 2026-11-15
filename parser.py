import aiohttp

MRKT_GQL = "https://graphql.getgems.io/graphql"

LISTINGS_QUERY = """
query NftSearch($count: Int!, $cursor: String) {
  alphaNftItemSearch(
    first: $count
    after: $cursor
    orderBy: { field: deployedAt, direction: DESC }
    filter: { saleType: [fix_price] }
  ) {
    edges {
      node {
        id
        name
        address
        sale {
          ... on NftSaleFixPrice {
            fullPrice
          }
        }
        collection {
          name
          floorPrice
        }
        content {
          ... on NftContentImage {
            originalUrl
          }
        }
        attributes {
          trait_type
          value
        }
      }
    }
  }
}
"""

COLLECTION_QUERY = """
query NftCollectionSearch($name: String!, $count: Int!) {
  alphaNftItemSearch(
    first: $count
    orderBy: { field: deployedAt, direction: DESC }
    filter: {
      saleType: [fix_price]
      collectionName: $name
    }
  ) {
    edges {
      node {
        id
        name
        address
        sale {
          ... on NftSaleFixPrice {
            fullPrice
          }
        }
        collection {
          name
          floorPrice
        }
        content {
          ... on NftContentImage {
            originalUrl
          }
        }
        attributes {
          trait_type
          value
        }
      }
    }
  }
}
"""

def _parse_node(node: dict) -> dict:
    """Привести GraphQL-ноду к единому формату карточки."""
    price_raw = 0
    sale = node.get("sale") or {}
    if sale.get("fullPrice"):
        price_raw = int(sale["fullPrice"])

    price_ton = price_raw / 1e9

    col      = node.get("collection") or {}
    floor_raw = col.get("floorPrice") or 0
    floor_ton = int(floor_raw) / 1e9 if floor_raw else 0

    # атрибуты → dict
    traits = {}
    for attr in node.get("attributes") or []:
        traits[attr.get("trait_type", "").lower()] = attr.get("value", "")

    # картинка
    content = node.get("content") or {}
    image   = content.get("originalUrl", "")

    # номер из имени (последнее слово после #  или просто последнее)
    name   = node.get("name", "")
    number = ""
    if "#" in name:
        number = name.split("#")[-1].strip()
    else:
        parts = name.rsplit(" ", 1)
        number = parts[-1] if len(parts) > 1 else name

    address = node.get("address", "")
    url     = f"https://getgems.io/nft/{address}" if address else ""

    return {
        "id":                node.get("id", ""),
        "name":              name,
        "number":            number,
        "collection":        col.get("name", ""),
        "price":             round(price_ton, 4),
        "floor_collection":  round(floor_ton, 4),
        "floor_model":       0,   # MRKT API не отдаёт флор модели напрямую
        "traits":            traits,
        "image":             image,
        "url":               url,
    }


class MrktParser:

    async def _gql(self, query: str, variables: dict) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                MRKT_GQL,
                json={"query": query, "variables": variables},
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_new_listings(self, count: int = 20) -> list[dict]:
        """Последние N листингов на MRKT."""
        try:
            data = await self._gql(LISTINGS_QUERY, {"count": count})
            edges = (
                data.get("data", {})
                    .get("alphaNftItemSearch", {})
                    .get("edges", [])
            )
            return [_parse_node(e["node"]) for e in edges if e.get("node")]
        except Exception as e:
            import logging
            logging.error(f"get_new_listings error: {e}")
            return []

    async def search_collection(self, name: str, limit: int = 5) -> list[dict]:
        """Поиск по названию коллекции."""
        try:
            data = await self._gql(COLLECTION_QUERY, {"name": name, "count": limit})
            edges = (
                data.get("data", {})
                    .get("alphaNftItemSearch", {})
                    .get("edges", [])
            )
            return [_parse_node(e["node"]) for e in edges if e.get("node")]
        except Exception as e:
            import logging
            logging.error(f"search_collection error: {e}")
            return []