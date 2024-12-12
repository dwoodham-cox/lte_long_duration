import argparse
from configparser import ConfigParser
from ncm import ncm

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

def main():
    """Module runner."""
    p = argparse.ArgumentParser(description="This script is used to move all router devices in one NCM group to a different group.")
    p.add_argument('source_group', action="store", help="The NCM ID of the source group.")
    p.add_argument('target_group', action="store", help="The NCM ID of the target group.")

    
    args: argparse.Namespace = p.parse_args()
    print(f"Moving all routers from group ID={args.source_group} to group ID={args.target_group}")

    n = ncm.NcmClientv2(api_keys=load_api_keys())
    source_router_ids = [router.get("id") for router in n.get_routers(group=args.source_group, limit="all")]
    print(f"Loaded IDs for {len(source_router_ids)} routers to be moved. Proceed? [y/N]")
    proceed = input()
    if proceed.strip().lower() == "y":
        for router_id in source_router_ids:
            result = n.assign_router_to_group(router_id=router_id, group_id=args.target_group)
            print(f"{router_id}: {result}")


if __name__ == "__main__":
    main()