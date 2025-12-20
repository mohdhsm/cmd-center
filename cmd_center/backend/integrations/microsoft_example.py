"""Example usage of Microsoft Graph API client."""

import asyncio
from microsoft_client import get_microsoft_client


async def example_sharepoint_operations():
    """Example SharePoint operations."""
    client = get_microsoft_client()

    try:
        # Get SharePoint sites
        print("Fetching SharePoint sites...")
        sites = await client.get_sharepoint_sites(search_query="teamsite")
        for site in sites:
            print(f"Site: {site.get('displayName')} - {site.get('webUrl')}")

        # Get a specific site by path
        site_id = "your-site-id"  # Replace with actual site ID
        print(f"\nFetching lists for site {site_id}...")
        lists = await client.get_sharepoint_lists(site_id)
        for lst in lists:
            print(f"List: {lst.get('displayName')} (ID: {lst.get('id')})")

        # Get items from a specific list
        list_id = "your-list-id"  # Replace with actual list ID
        print(f"\nFetching items from list {list_id}...")
        items = await client.get_sharepoint_list_items(
            site_id=site_id,
            list_id=list_id,
            top=10
        )
        for item in items:
            print(f"Item {item.id}: {item.fields}")

        # Create a new list item
        new_item = await client.create_sharepoint_list_item(
            site_id=site_id,
            list_id=list_id,
            fields={
                "Title": "New Item",
                "Description": "Created via API"
            }
        )
        print(f"\nCreated new item: {new_item.id}")

    finally:
        await client.close()


async def example_onedrive_operations():
    """Example OneDrive operations."""
    client = get_microsoft_client()

    try:
        # Get file metadata using file ID
        print("Fetching file metadata...")
        file_metadata = await client.get_onedrive_file_metadata(
            file_id="your-file-id",  # Replace with actual file ID
            user_id="user@domain.com"  # Optional: specify user
        )
        print(f"File: {file_metadata.name}")
        print(f"Size: {file_metadata.size} bytes")
        print(f"Last modified: {file_metadata.last_modified_datetime}")
        print(f"Web URL: {file_metadata.web_url}")

        # Download a file
        print("\nDownloading file...")
        file_content = await client.download_onedrive_file(
            file_path="/Documents/example.xlsx",  # Or use file_id
            user_id="user@domain.com"
        )
        print(f"Downloaded {len(file_content)} bytes")

        # Save the file locally
        with open("downloaded_file.xlsx", "wb") as f:
            f.write(file_content)
        print("File saved as downloaded_file.xlsx")

        # List files in a folder
        print("\nListing files in Documents folder...")
        files = await client.list_onedrive_folder(
            folder_path="/Documents",
            user_id="user@domain.com"
        )
        for file in files:
            print(f"- {file.name} ({file.size} bytes)")

    finally:
        await client.close()


async def main():
    """Run examples."""
    print("=== SharePoint Examples ===")
    await example_sharepoint_operations()

    print("\n=== OneDrive Examples ===")
    await example_onedrive_operations()


if __name__ == "__main__":
    asyncio.run(main())
