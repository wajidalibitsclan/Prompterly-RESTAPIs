#!/usr/bin/env python3
"""
Migration script to setup Stripe products for existing paid lounges.

This script finds all paid lounges that don't have Stripe product IDs
and creates the corresponding Stripe Product and Prices for each.

Usage:
    python -m scripts.migrate_existing_lounges_to_stripe

Or from the project root:
    python scripts/migrate_existing_lounges_to_stripe.py
"""
import asyncio
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.lounge import Lounge, AccessType
from app.services.billing_service import billing_service


async def migrate_existing_paid_lounges(db: Session, dry_run: bool = False) -> dict:
    """
    Setup Stripe products for existing paid lounges without Stripe IDs.

    Args:
        db: Database session
        dry_run: If True, only report what would be done without making changes

    Returns:
        Dictionary with migration results
    """
    results = {
        "total_paid_lounges": 0,
        "already_migrated": 0,
        "successfully_migrated": 0,
        "failed": 0,
        "errors": []
    }

    # Find all paid lounges
    paid_lounges = db.query(Lounge).filter(
        Lounge.access_type == AccessType.PAID
    ).all()

    results["total_paid_lounges"] = len(paid_lounges)
    print(f"\nFound {len(paid_lounges)} paid lounges")

    for lounge in paid_lounges:
        if lounge.stripe_product_id:
            print(f"  ✓ Lounge {lounge.id} ({lounge.title}) - Already has Stripe product: {lounge.stripe_product_id}")
            results["already_migrated"] += 1
            continue

        if dry_run:
            print(f"  → Lounge {lounge.id} ({lounge.title}) - Would create Stripe product")
            results["successfully_migrated"] += 1
            continue

        try:
            print(f"  → Creating Stripe product for lounge {lounge.id} ({lounge.title})...", end=" ")

            stripe_data = await billing_service.create_lounge_stripe_product(
                lounge_id=lounge.id,
                lounge_title=lounge.title,
                lounge_slug=lounge.slug,
                db=db
            )

            lounge.stripe_product_id = stripe_data['stripe_product_id']
            lounge.stripe_monthly_price_id = stripe_data['stripe_monthly_price_id']
            lounge.stripe_yearly_price_id = stripe_data['stripe_yearly_price_id']

            db.commit()

            print(f"✓ Product: {stripe_data['stripe_product_id']}")
            print(f"    Monthly: {stripe_data['stripe_monthly_price_id']}")
            print(f"    Yearly: {stripe_data['stripe_yearly_price_id']}")

            results["successfully_migrated"] += 1

        except Exception as e:
            print(f"✗ Failed: {str(e)}")
            results["failed"] += 1
            results["errors"].append({
                "lounge_id": lounge.id,
                "title": lounge.title,
                "error": str(e)
            })

    return results


def main():
    """Main entry point for the migration script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate existing paid lounges to have Stripe products"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Lounge Stripe Migration Script")
    print("=" * 60)

    if args.dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***\n")
    else:
        print("\n*** LIVE MODE - Changes will be committed to Stripe and database ***\n")

        if not args.force:
            confirm = input("Are you sure you want to proceed? (yes/no): ")
            if confirm.lower() != "yes":
                print("Aborted.")
                sys.exit(0)

    # Create database session
    db = SessionLocal()

    try:
        # Run the migration
        results = asyncio.run(migrate_existing_paid_lounges(db, dry_run=args.dry_run))

        # Print summary
        print("\n" + "=" * 60)
        print("Migration Summary")
        print("=" * 60)
        print(f"Total paid lounges:     {results['total_paid_lounges']}")
        print(f"Already migrated:       {results['already_migrated']}")
        print(f"Successfully migrated:  {results['successfully_migrated']}")
        print(f"Failed:                 {results['failed']}")

        if results["errors"]:
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  - Lounge {error['lounge_id']} ({error['title']}): {error['error']}")

        if args.dry_run:
            print("\n*** This was a dry run. Run without --dry-run to apply changes. ***")

    finally:
        db.close()


if __name__ == "__main__":
    main()
