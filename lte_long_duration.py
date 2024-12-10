"""A script to query the NCM API for devices that are stuck in LTE backup mode.

Derek Woodham (derek.woodham@cox.com)
"""

from configparser import ConfigParser
from datetime import datetime, timedelta, timezone
from ncm import ncm
from prettytable import PrettyTable


def load_api_keys(f: str = "apikeys.ini") -> dict:
    """Read API keys from file."""
    cp = ConfigParser()
    cp.read([f])
    return {
        "X-CP-API-ID": cp["KEYS"]["x-cp-api-id"],
        "X-CP-API-KEY": cp["KEYS"]["x-cp-api-key"],
        "X-ECM-API-ID": cp["KEYS"]["x-ecm-api-id"],
        "X-ECM-API-KEY": cp["KEYS"]["x-ecm-api-key"],
    }


def get_lte_usage_time_window(days: int = 1) -> tuple[str, str]:
    """Returns datetime strings to use when querying NCM for usage samples."""
    today = datetime.now(timezone.utc)
    start = today - timedelta(days=days)
    return (
        f"{start.year}-{start.month}-{start.day}T00:00:00.000000+00:00",
        f"{today.year}-{today.month}-{today.day}T00:00:00.000000+00:00",
    )


def main():
    """Module runner."""

    tbl = PrettyTable()
    tbl.field_names = [
        "Router ID",
        "Router Name",
        "Router MAC",
        "Router Serial",
        "LTE Provider",
        "ICCID",
        "LTE Uptime",
        "24Hr LTE Usage (GB)",
        "EWAN Link State",
        "EWAN IP Address",
    ]

    n = ncm.NcmClientv2(api_keys=load_api_keys())

    # IDs of the IBC-PROD groups
    production_groups = [
        "225264",  # IBC-PROD-E100-1
        "225265",  # IBC-PROD-E100-2
        "225266",  # IBC-PROD-E100-3
        "225267",  # IBC-PROD-E100-4
        "201772",  # IBC-PROD-E300-1
        "199428",  # IBC-PROD-E300-2
        "199430",  # IBC-PROD-E300-3
        "199432",  # IBC-PROD-E300-4
    ]
    production_group_urls = [
        f"https://www.cradlepointecm.com/api/v2/groups/{group_id}/"
        for group_id in production_groups
    ]

    # Set LTE usage sample window to the previous day
    lte_usage_time_window = get_lte_usage_time_window(days=1)

    net_devices = n.get_net_devices(
        connection_state="connected", is_asset="true", expand="router", limit="all"
    )

    # Sort by longest LTE uptime
    net_devices.sort(key=lambda d: d.get("uptime", 0), reverse=True)

    # Discard net_devices with LTE uptime less than 1 week
    net_devices = list(
        filter(lambda d: d.get("uptime", 0) >= 7 * 24 * 60 * 60, net_devices)
    )

    # Discard net_devices not in production groups
    net_devices = list(
        filter(
            lambda d: d.get("router", {}).get("group", "") in production_group_urls,
            net_devices,
        )
    )

    for nd in net_devices:
        router = nd.get("router", {})
        router_id = router.get("id")

        ewan_link = ""
        ewan_ipv4_addr = ""
        if router_id:
            router_nds = n.get_net_devices_for_router(router_id)
            ethwan_nds = list(
                filter(lambda d: d.get("name") == "ethernet-wan", router_nds)
            )
            if ethwan_nds:
                ethwan_nd = ethwan_nds[0]
                ewan_link = ethwan_nd.get("connection_state")
                ewan_ipv4_addr = ethwan_nd.get("ipv4_address")

        print(f"Getting net_device_usage_samples for router {router_id}")
        usage_samples = n.get_net_device_usage_samples(
            net_device=nd.get("id"),
            created_at__gt=lte_usage_time_window[0],
            created_at__lt=lte_usage_time_window[1],
            limit="all",
        )
        print(f"Retrieved {len(usage_samples)} usage samples for router {router_id}.")
        usage_bytes = sum(
            sample.get("bytes_in", 0) + sample.get("bytes_out", 0)
            for sample in usage_samples
        )

        tbl.add_row(
            [
                router_id,
                router.get("name"),
                router.get("mac"),
                router.get("serial_number"),
                nd.get("homecarrid"),
                nd.get("iccid"),
                timedelta(seconds=nd.get("uptime", 0)),
                round(usage_bytes / (1_000_000_000), 2),  # Display usage in GB
                ewan_link,
                ewan_ipv4_addr,
            ]
        )

    print(tbl)
    print(f"Row count: {len(net_devices)}")
    with open("results.csv", "w", encoding="utf-8") as f:
        f.write(tbl.get_csv_string())


if __name__ == "__main__":
    main()
