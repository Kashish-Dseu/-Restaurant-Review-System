#!/usr/bin/env python3
"""
Show all restaurant names from the database
"""

import sqlite3

def show_restaurants():
    conn = sqlite3.connect('restaurant_reviews.db')
    c = conn.cursor()
    
    # Get total count
    c.execute('SELECT COUNT(*) FROM restaurants')
    total = c.fetchone()[0]
    
    print("=" * 80)
    print(f"RESTAURANT DATABASE - {total} RESTAURANTS")
    print("=" * 80)
    print()
    
    # Show some popular chains
    print("🍔 POPULAR CHAINS:")
    print("-" * 80)
    chains = ['KFC', 'Pizza Hut', 'Starbucks', 'Subway', 'Burger King', 
              'McDonald\'s', 'Domino\'s Pizza', 'Baskin Robbins']
    
    for chain in chains:
        c.execute('SELECT name, cuisine, location FROM restaurants WHERE name LIKE ?', (f'%{chain}%',))
        result = c.fetchone()
        if result:
            print(f"✓ {result[0]:40} - {result[2]}")
    
    print()
    print("🍛 LOCAL FAVORITES:")
    print("-" * 80)
    locals = ['Paradise Biryani', 'Shah Ghouse', 'Cafe Niloufer', 
              'Karachi Bakery', 'Minerva']
    
    for local in locals:
        c.execute('SELECT name, cuisine, location FROM restaurants WHERE name LIKE ?', (f'%{local}%',))
        result = c.fetchone()
        if result:
            print(f"✓ {result[0]:40} - {result[2]}")
    
    print()
    print("📋 ALL RESTAURANTS (First 50):")
    print("-" * 80)
    
    c.execute('SELECT id, name, cuisine, location FROM restaurants ORDER BY id LIMIT 50')
    for row in c.fetchall():
        print(f"{row[0]:3}. {row[1]:45} {row[3]:15} - {row[2][:30]}")
    
    print()
    print(f"... and {total - 50} more restaurants!")
    print()
    print("=" * 80)
    print(f"✅ TOTAL: {total} REAL RESTAURANTS LOADED FROM CSV")
    print("=" * 80)
    
    # Show cuisine statistics
    print()
    print("📊 TOP CUISINE CATEGORIES:")
    print("-" * 80)
    c.execute('''
        SELECT cuisine, COUNT(*) as count 
        FROM restaurants 
        GROUP BY cuisine 
        ORDER BY count DESC 
        LIMIT 15
    ''')
    
    for cuisine, count in c.fetchall():
        cuisine_short = cuisine[:60] + "..." if len(cuisine) > 60 else cuisine
        print(f"{cuisine_short:65} : {count:3} restaurants")
    
    conn.close()

if __name__ == '__main__':
    show_restaurants()
