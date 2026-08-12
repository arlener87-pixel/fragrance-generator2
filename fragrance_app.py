#!/usr/bin/env python3
"""
Fragrance Generator + Layering Combo Suggester
- Recommends Top 1 / Top 3 / Top 5 single fragrances
- Suggests complementary layering combinations
- Supports Male, Female, Unisex, and Any gender filters
"""

import random
import re
from typing import List, Dict, Tuple

# ====================== FRAGRANCE DATABASE ======================
FRAGRANCES = [
    {"name": "Ajwad", "brand": "Lattafa", "gender": "Unisex", "season": "Versatile (cooler preferred)", "notes": "Fruity-woody-oriental (pineapple/rose/oud-leaning)", "category": ["Oriental", "Woody", "Fruity"]},
    {"name": "Al Rehab Caramello", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Pistachio, Almond / Heart – Jasmine, Heliotrope / Base – Caramel, Vanilla, Sandalwood", "category": ["Gourmand", "Sweet"]},
    {"name": "Al Rehab Chocomusk", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Warm Spicy, Amber / Heart – Sweet, Powdery, Vanilla / Base – Chocolate, Musky, Cocoa", "category": ["Gourmand", "Sweet"]},
    {"name": "Al Rehab Chocomusk Marshmallow", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Marshmallow, Strawberry / Heart – Cocoa, Vanilla / Base – Sweet Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Al Rehab Chocomusk Vanilla", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Chocolate / Heart – Vanilla / Base – Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Al Rehab Cup Cake", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Citrus, Amber / Heart – Vanilla Cake / Base – Vanilla, Amber", "category": ["Gourmand", "Sweet"]},
    {"name": "Al Rehab French Vanilla", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Vanilla / Heart – Creamy Sweet / Base – Vanilla, Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Al Rehab Royal Men", "brand": "Al Rehab", "gender": "Male", "season": "Fall, Winter", "notes": "Top – Spicy, Citrus, Woody / Heart – Floral, Sweet / Base – Amber, Musk, Vanilla", "category": ["Woody", "Spicy", "Oriental"]},
    {"name": "Al Rehab Silver", "brand": "Al Rehab", "gender": "Unisex/Male", "season": "Spring, Summer", "notes": "Top – Fresh Citrus, Metallic / Heart – Floral / Base – Musk, Sweet", "category": ["Fresh", "Citrus"]},
    {"name": "Al Rehab Soft", "brand": "Al Rehab", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top – Citruses / Heart – Orchid, Jasmine, Vanilla, Caramel / Base – White Musk, Woody Notes, Vetiver", "category": ["Floral", "Sweet", "Gourmand"]},
    {"name": "Ameerat Al Arab Prive Rose", "brand": "Ameerat Al Arab", "gender": "Female", "season": "Fall, Spring", "notes": "Top – Rose / Heart – Floral, Sweet / Base – Musk, Vanilla", "category": ["Floral", "Sweet"]},
    {"name": "Arabiyat Prestige Bahiya Garnet", "brand": "Arabiyat Prestige", "gender": "Female-leaning", "season": "Fall, Winter", "notes": "Top – Cherry, Mandarin, Mango, Pear, Bergamot / Heart – Amber, Fig, Jasmine / Base – Amber, Vanilla, Sandalwood, Musk", "category": ["Fruity", "Oriental", "Sweet"]},
    {"name": "Arabiyat Prestige Nyla", "brand": "Arabiyat Prestige", "gender": "Female", "season": "Spring, Summer", "notes": "Top – Coconut, Peach, Bergamot, Mandarin / Heart – Tiare, White Flowers, Jasmine, Rose / Base – White Musk, Patchouli", "category": ["Floral", "Fruity", "Fresh"]},
    {"name": "Arabiyat Prestige Nyla Vanielle", "brand": "Arabiyat Prestige", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Jasmine, Vanilla Bean / Heart – Caramel, Amber / Base – Musk, Tonka Bean, Vanilla", "category": ["Gourmand", "Sweet", "Floral"]},
    {"name": "Ard Al Zaafaran Bint Hooran", "brand": "Ard Al Zaafaran", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Almond, Coffee, Ylang Ylang / Heart – Jasmine, Rose, Tuberose / Base – Vanilla, Musk, Tonka, Woody/Cacao", "category": ["Gourmand", "Floral", "Oriental"]},
    {"name": "Armaf Island Bliss", "brand": "Armaf", "gender": "Unisex", "season": "Spring, Summer", "notes": "Top – Tropical Fruits, Coconut / Heart – Sweet / Base – Musk", "category": ["Fruity", "Fresh", "Sweet"]},
    {"name": "Armaf Odyssey Aqua", "brand": "Armaf", "gender": "Male", "season": "Spring, Summer", "notes": "Top – Orange, Grapefruit, Artemisia / Heart – Mint, Lavender / Base – Ambroxan, Cypress, Patchouli", "category": ["Fresh", "Citrus", "Aromatic"]},
    {"name": "Armaf Odyssey Candee", "brand": "Armaf", "gender": "Female-leaning", "season": "Fall, Winter", "notes": "Top – Strawberry, Raspberry, Peach, Bergamot / Heart – Caramel, Jasmine / Base – Patchouli, Musk, Amber", "category": ["Fruity", "Gourmand", "Sweet"]},
    {"name": "Armaf Odyssey Marshmallow", "brand": "Armaf", "gender": "Unisex", "season": "Spring, Fall, Winter", "notes": "Top – Apple, Lemon, Coconut, Peony, Lily of the Valley / Heart – Strawberry, Peach, Raspberry, Apricot, Marshmallow, Orange Blossom / Base – Vanilla, Praline, Tonka, Amber, Musk, Mascarpone", "category": ["Gourmand", "Fruity", "Sweet"]},
    {"name": "Banat Dubai", "brand": "Le Chameau", "gender": "Female", "season": "Versatile to cooler", "notes": "Top – Jasmine, Bergamot, Peony / Heart – Pineapple, Peach, Plum / Base – Musk, Patchouli, Sandalwood", "category": ["Floral", "Fruity"]},
    {"name": "Baraja Red 500", "brand": "Baraja", "gender": "Unisex/Male", "season": "Fall, Winter", "notes": "Top – Red Fruits, Spices / Heart – Sweet Notes / Base – Woody, Musk", "category": ["Fruity", "Woody", "Spicy"]},
    {"name": "Bellavita Vanilla", "brand": "Bellavita", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Aldehydes, Heliotrope, Coconut, Vanilla / Heart – Vanilla, Mango / Base – White Musk, Coconut, Vanilla Absolute", "category": ["Gourmand", "Sweet"]},
    {"name": "Berries Cream Macaron", "brand": "Arabiyat Sugar", "gender": "Female", "season": "Spring–Fall", "notes": "Berry + cream macaron gourmand", "category": ["Gourmand", "Fruity", "Sweet"]},
    {"name": "Black Opinion", "brand": "Black Opinion", "gender": "Male/Unisex", "season": "Fall–Winter", "notes": "Dark, bold (woody/spicy/leather)", "category": ["Woody", "Spicy", "Leather"]},
    {"name": "Blue for Men Le Parfum", "brand": "Blue for Men", "gender": "Male/Unisex", "season": "Fall, Winter", "notes": "Top – Cardamom / Heart – Lavender, Iris / Base – Vanilla, Oriental Woods", "category": ["Woody", "Oriental", "Spicy"]},
    {"name": "Caramel Chocolate Macaron", "brand": "Arabiyat Sugar", "gender": "Female/Unisex", "season": "Fall–Winter", "notes": "Caramel-chocolate-macaron gourmand", "category": ["Gourmand", "Sweet"]},
    {"name": "Club de Nuit Women", "brand": "Armaf", "gender": "Female", "season": "Spring, Fall", "notes": "Top – Apple, Citrus / Heart – Rose, Jasmine / Base – Vanilla, Musk", "category": ["Floral", "Fruity", "Fresh"]},
    {"name": "Coconut Chiffon", "brand": "Arabiyat Sugar", "gender": "Female/Unisex", "season": "Spring–Summer", "notes": "Coconut + light cake/chiffon", "category": ["Gourmand", "Sweet", "Fresh"]},
    {"name": "Confections", "brand": "Paris Corner", "gender": "Female/Unisex", "season": "Fall–Winter", "notes": "Gourmand/sweet, confectionery-style", "category": ["Gourmand", "Sweet"]},
    {"name": "Dulzura", "brand": "Paris Corner", "gender": "Female", "season": "Fall–Winter", "notes": "Top – Black pepper, buttermilk / Heart – Cake, vanilla, cream / Base – Amber, musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Eclaire Banoffi", "brand": "Lattafa", "gender": "Unisex/Female", "season": "Fall–Winter", "notes": "Banana-toffee/éclair gourmand", "category": ["Gourmand", "Sweet"]},
    {"name": "Éclat Parfumerie Al Gazal", "brand": "Éclat Parfumerie", "gender": "Unisex (leans masculine)", "season": "Versatile to cooler", "notes": "Limited public data; typically woody-oriental or spicy", "category": ["Woody", "Oriental"]},
    {"name": "Elyssia Aura", "brand": "Riiffs", "gender": "Unisex", "season": "Fall, Winter (versatile to cooler)", "notes": "Top – Cinnamon, Orange, Nutmeg / Heart – Vanilla Cream, Cognac, Cocoa / Base – Bourbon Vanilla, Cedarwood, Patchouli", "category": ["Gourmand", "Spicy", "Woody"]},
    {"name": "Elyssia Scarlet", "brand": "Riiffs", "gender": "Female", "season": "Spring–Summer / versatile", "notes": "Top – Black Cherry, Pink Pepper / Heart – Leather, Cream, Benzoin / Base – Vanilla Absolute, Cashmeran, Amber, Iso E Super", "category": ["Fruity", "Leather", "Sweet"]},
    {"name": "Emir Pear Potion", "brand": "Paris Corner", "gender": "Unisex", "season": "Spring", "notes": "Top – Pear, Apple / Heart – Caramel, Jasmine / Base – Raspberry, Musk", "category": ["Fruity", "Gourmand", "Sweet"]},
    {"name": "Empire Najm by Risala", "brand": "Risala", "gender": "Unisex (female-leaning)", "season": "Fall, Winter", "notes": "Top – Mango, Ginger, Lemon, Red Berries / Heart – Coumarin, Jasmine, Cedar / Base – Cypriol, Amber, Musk, Oud", "category": ["Fruity", "Oriental", "Woody"]},
    {"name": "Emper Boulevard of New York", "brand": "Le Chameau", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Roasted Coffee Beans / Heart – Praline, Rose / Base – Oakmoss, Cedar, Amber", "category": ["Gourmand", "Woody"]},
    {"name": "Entice Extrait", "brand": "Vurv", "gender": "Female", "season": "Cooler / evening", "notes": "Richer/intensified sweet/fruity or oriental", "category": ["Oriental", "Sweet", "Fruity"]},
    {"name": "Entice Ruby", "brand": "Vurv", "gender": "Female", "season": "Spring–Summer / versatile", "notes": "Fruity-floral / berry-red fruit leaning", "category": ["Fruity", "Floral"]},
    {"name": "Espada Intense", "brand": "Le Chameau", "gender": "Male", "season": "Cooler seasons / evening", "notes": "Deeper/intensified version of Espada Prime", "category": ["Woody", "Spicy"]},
    {"name": "Espada Prime", "brand": "Le Chameau", "gender": "Male", "season": "Spring–Summer / versatile", "notes": "Fresh or spicy-woody", "category": ["Fresh", "Woody", "Spicy"]},
    {"name": "Fakhama", "brand": "Amaran", "gender": "Unisex/Male", "season": "Cooler seasons", "notes": "Luxury oriental or woody", "category": ["Oriental", "Woody"]},
    {"name": "Fragrance World Crème of Clouds", "brand": "Fragrance World", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Vanilla, Chocolate, Burnt Sugar / Heart – Milk, Creamy/Coconut Milk, Whipped Cream / Base – Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "French Avenue 8th Wonder", "brand": "French Avenue", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Cardamom, Pink Pepper, Candy Apple / Heart – Liquor, Dates, Boozy notes, Davana, Osmanthus / Base – Myrrh, Benzoin, Styrax, Amber Xtreme, Labdanum, Patchouli", "category": ["Oriental", "Spicy", "Sweet"]},
    {"name": "French Avenue Spectre Original", "brand": "French Avenue", "gender": "Male/Unisex (leans masculine)", "season": "Fall, Winter", "notes": "Top – Incense, Guaiac Wood, Saffron / Heart – Leather, Amberwood, Violet, Sugar Cane / Base – Smoke, Patchouli, Sandalwood, Woodsy Notes, Black Musk", "category": ["Woody", "Leather", "Oriental"]},
    {"name": "French Avenue Vulcan Baie", "brand": "French Avenue", "gender": "Unisex", "season": "Spring, Summer", "notes": "Top – Blackberry, Black Currant, Rosemary, Bergamot / Heart – Raspberry, Vodka, Basil, Lily of the Valley / Base – Strawberry, Musk, Peach, Amber, Sandalwood, Patchouli, Incense", "category": ["Fruity", "Fresh", "Aromatic"]},
    {"name": "French Vanilla Latte", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Nutella, Cardamom, Rum / Heart – Cocoa, Coconut, White Flowers, Lily of the Valley / Base – Sandalwood, Ambergris, Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Ghaliya", "brand": "Zakat", "gender": "Unisex/Female", "season": "Fall–Winter", "notes": "Rich oriental/oud-floral", "category": ["Oriental", "Floral", "Oud"]},
    {"name": "Gulf Orchid Cookie Bite", "brand": "Gulf Orchid", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Cookie, Butter / Heart – Vanilla, Musk / Base – Caramel, Amber", "category": ["Gourmand", "Sweet"]},
    {"name": "Gulf Orchid Piña Colada Musk Collection Body Spray", "brand": "Gulf Orchid", "gender": "Unisex", "season": "Spring, Summer", "notes": "Top – Pineapple, Coconut / Heart – Tropical / Base – Musk", "category": ["Fruity", "Fresh", "Sweet"]},
    {"name": "Hawas Elixir", "brand": "Rasasi", "gender": "Unisex", "season": "Fall–Winter", "notes": "Top – Mint, bergamot, artemisia / Heart – Dark chocolate, lavender, benzoin / Base – Vanilla, tonka bean, white musk", "category": ["Gourmand", "Fresh", "Sweet"]},
    {"name": "Heroes Energize", "brand": "Heroes", "gender": "Male", "season": "Spring, Summer", "notes": "Top – Citrus, Aromatic Herbs / Heart – Light Spices / Base – Woods, Musk", "category": ["Fresh", "Citrus", "Aromatic"]},
    {"name": "Kandy Rush", "brand": "Kandy Rush", "gender": "Female/Unisex", "season": "Fall–Winter / casual year-round", "notes": "Sweet candy/gourmand", "category": ["Gourmand", "Sweet"]},
    {"name": "Khadlaj Cafe Latte", "brand": "Khadlaj", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Coffee, Sweet Almond, Milk / Heart – Vanilla, Ice Cream Accord, Amber / Base – Vanilla, Almond Cream, Caramel", "category": ["Gourmand", "Sweet"]},
    {"name": "Khadlaj Cream Velvet", "brand": "Khadlaj", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top – Caramel, Butter / Heart – Tonka, Honey, Jasmine / Base – Vanilla, Musk, Amber", "category": ["Gourmand", "Sweet"]},
    {"name": "Khadlaj Hareem Al Sultan Gold", "brand": "Khadlaj", "gender": "Female", "season": "Spring, Summer", "notes": "Top – Bergamot, Jasmine, Peony / Heart – Pineapple, Peach, Plum / Base – Musk, Sandalwood, Patchouli", "category": ["Floral", "Fruity", "Fresh"]},
    {"name": "Khadlaj Nuha Vanilla Pearl", "brand": "Khadlaj", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Blackcurrant, Strawberry, Freesia / Heart – Raspberry, Magnolia, Cashmere Wood / Base – Vanilla, Caramel, Moss", "category": ["Fruity", "Gourmand", "Floral"]},
    {"name": "Khadlaj Peach Velvet", "brand": "Khadlaj", "gender": "Female", "season": "Spring, Summer, Fall", "notes": "Top – Guava, Peach, Nectarine / Heart – Vanilla, Ginger, Cinnamon, Amber / Base – Caramel, Musk, Sandalwood", "category": ["Fruity", "Gourmand", "Sweet"]},
    {"name": "Khadlaj Zainab Oil", "brand": "Khadlaj", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Bergamot, Gardenia, Almond / Heart – Coconut, Caramel / Base – Patchouli, Vanilla, Musk", "category": ["Gourmand", "Floral", "Sweet"]},
    {"name": "Khamrah Waha", "brand": "Lattafa", "gender": "Unisex", "season": "Fall–Winter", "notes": "Spicy-sweet (date, cinnamon, vanilla family)", "category": ["Oriental", "Spicy", "Sweet"]},
    {"name": "Khayali Vanilla Ayelet", "brand": "Khayali", "gender": "Unisex", "season": "Fall–Winter", "notes": "Vanilla orchid, jasmine / Brown sugar, tonka / Amber, musk, patchouli (Kayali-inspired)", "category": ["Gourmand", "Floral", "Sweet"]},
    {"name": "Lattafa Angham", "brand": "Lattafa", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top – Ginger, Mandarin, Pink Pepper / Heart – Lavender, Praline, Cacao, Jasmine / Base – Vanilla, Amber, Musk", "category": ["Gourmand", "Spicy", "Sweet"]},
    {"name": "Lattafa Ansaam Gold", "brand": "Lattafa", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top – Mandarin Orange, Pear / Heart – Sweet Notes, Jasmine, Rose / Base – Musk, Vanilla, Raspberry", "category": ["Fruity", "Floral", "Sweet"]},
    {"name": "Lattafa Asad", "brand": "Lattafa", "gender": "Male", "season": "Fall, Winter", "notes": "Top – Black Pepper, Tobacco, Pineapple / Heart – Patchouli, Coffee, Iris / Base – Vanilla, Amber, Dry Woods, Benzoin, Labdanum", "category": ["Woody", "Spicy", "Oriental"]},
    {"name": "Lattafa Badee Al Oud Noble Blush", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Rose Milk / Heart – Meringue, Almond / Base – Vanilla, Musk, Sandalwood", "category": ["Floral", "Gourmand", "Sweet"]},
    {"name": "Lattafa Coral (Ana Abiyedh Coral)", "brand": "Lattafa", "gender": "Unisex (leans feminine)", "season": "Spring, Summer", "notes": "Top – Watermelon, Peach, Orange / Heart – Coconut, White Flowers / Base – Musk, Vanilla, Amber", "category": ["Fruity", "Fresh", "Sweet"]},
    {"name": "Lattafa Dalal", "brand": "Lattafa", "gender": "Female", "season": "Spring", "notes": "Top – Apple (Golden Delicious), Mandarin / Heart – Jasmine, Ylang-Ylang, Orange Flower / Base – Vanilla, Musk, Oakmoss", "category": ["Floral", "Fruity", "Fresh"]},
    {"name": "Lattafa Eclaire", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Caramel, Milk, Sugar / Heart – Honey, White Flowers / Base – Vanilla, Praline, Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Lattafa Emaan", "brand": "Lattafa", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top – Orange Blossom, Black Currant, Bergamot / Heart – Tuberose, Jasmine, Marigold / Base – Musk, Vanilla, Cedarwood, Patchouli", "category": ["Floral", "Fruity"]},
    {"name": "Lattafa Eternal Vanille", "brand": "Lattafa", "gender": "Unisex", "season": "Year-round (best Spring/Fall)", "notes": "Top – Blackberry / Heart – Cocoapulse, Vanilla Caviar, Cacao / Base – Akigalawood, Tonka Bean, Ambrofix, Cedarwood, Benzoin, Musk", "category": ["Gourmand", "Woody", "Sweet"]},
    {"name": "Lattafa Fakhar Black", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Dark Fruits, Spices / Heart – Woody / Base – Vanilla, Musk", "category": ["Fruity", "Woody", "Spicy"]},
    {"name": "Lattafa Fakhar Gold", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Tuberose, Salt / Heart – Amber, Tonka / Base – Cedarwood, Vetiver, Labdanum", "category": ["Floral", "Woody", "Oriental"]},
    {"name": "Lattafa Habik (Women’s version)", "brand": "Lattafa", "gender": "Female", "season": "Spring, Summer", "notes": "Top – Pear, Bergamot / Heart – Lily of the Valley, Jasmine, Freesia / Base – Musk, Amber, Oakmoss", "category": ["Floral", "Fresh", "Fruity"]},
    {"name": "Lattafa Haya", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Champagne, Strawberry, Rose, Tangerine, Blood Orange / Heart – Gardenia, Jasmine, Vanilla Orchid / Base – Amber, Sandalwood", "category": ["Floral", "Fruity", "Sweet"]},
    {"name": "Lattafa Her Confessions", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Cinnamon / Heart – Tuberose, Jasmine, Incense / Base – Vanilla, Musk, Tonka", "category": ["Floral", "Spicy", "Oriental"]},
    {"name": "Lattafa His Confessions", "brand": "Lattafa", "gender": "Male", "season": "Fall, Winter", "notes": "Top – Lavender, Cinnamon, Mandarin / Heart – Iris, Benzoin, Cypress, Mahonial / Base – Vanilla, Tonka, Amber, Incense, Cedarwood, Patchouli", "category": ["Woody", "Spicy", "Oriental"]},
    {"name": "Lattafa Khamrah Dukhan", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Spices, Pimento, Mandarin / Heart – Incense, Labdanum, Orange Blossom, Patchouli / Base – Tobacco, Praline, Amber, Tonka Bean, Benzoin", "category": ["Oriental", "Spicy", "Sweet"]},
    {"name": "Lattafa Khamrah Original", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Cinnamon, Nutmeg, Bergamot / Heart – Dates, Praline, Tuberose, Mahonial / Base – Vanilla, Tonka Bean, Amberwood, Myrrh, Benzoin, Akigalawood", "category": ["Oriental", "Spicy", "Sweet"]},
    {"name": "Lattafa Khamrah Qahwa", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Cinnamon, Cardamom, Ginger / Heart – Praline, Candied Fruits, White Flowers / Base – Coffee, Vanilla, Tonka Bean, Benzoin, Musk", "category": ["Gourmand", "Spicy", "Sweet"]},
    {"name": "Lattafa Maitha Oil (Attar)", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Anise / Heart – Caramel / Base – Vanilla, Tonka Bean, Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Lattafa Mayar Cherry Intense", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Strawberry, Bergamot / Heart – Cherry Jam, Cacao / Base – Vanilla, Amber, Patchouli", "category": ["Fruity", "Gourmand", "Sweet"]},
    {"name": "Lattafa Nasmaat", "brand": "Lattafa", "gender": "Unisex", "season": "Spring, Fall", "notes": "Top – Blackcurrant, Apricot, Pineapple / Heart – Magnolia, Cyclamen, Jasmine, Orange Blossom, Rose / Base – Vanilla, Cashmeran, Caramel, Sandalwood", "category": ["Floral", "Fruity", "Sweet"]},
    {"name": "Lattafa Nebras", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Red Berries, Mandarin Orange / Heart – Vanilla, Cacao, Rose / Base – Sugar, Tonka Bean, Amber, Musk", "category": ["Gourmand", "Fruity", "Sweet"]},
    {"name": "Lattafa Nebras Elixir", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter, Mild Spring", "notes": "Top – Milk Candy, Whipped Cream / Heart – Sugar Cane, Heliotrope / Base – Vanilla, Ambroxan, Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Lattafa Opulent Dubai", "brand": "Lattafa", "gender": "Unisex", "season": "Spring, Summer (versatile year-round in mild climates)", "notes": "Top – Mango, Grapefruit, Lemon, Ginger / Heart – Jasmine, Cedarwood, Violet / Base – Woodsy notes, Ambergris, Benzoin, Oakmoss", "category": ["Fruity", "Woody", "Fresh"]},
    {"name": "Lattafa Oud Mood", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Rose, Saffron, Pimento / Heart – Agarwood (Oud), Caramel, Floral Notes, Patchouli / Base – Woody Notes, Amber, Resins, Incense, Musk", "category": ["Oriental", "Oud", "Woody"]},
    {"name": "Lattafa Qaed Al Fursan (Original)", "brand": "Lattafa", "gender": "Unisex (leans masculine)", "season": "Versatile", "notes": "Top – Pineapple, Saffron / Heart – Balsam Fir, Jasmine / Base – Cedar, Amber, Agarwood (Oud)", "category": ["Fruity", "Woody", "Oud"]},
    {"name": "Lattafa Qaed Al Fursan Unlimited", "brand": "Lattafa", "gender": "Male/Unisex", "season": "Spring, Fall", "notes": "Top – Coconut, Pineapple, Citruses / Heart – Ylang-Ylang, Frangipani, Jasmine / Base – Vanilla, Musk, Sandalwood, Sweet Notes", "category": ["Fruity", "Floral", "Sweet"]},
    {"name": "Lattafa Qaed Al Fursan Untamed", "brand": "Lattafa", "gender": "Male/Unisex", "season": "Spring, Fall", "notes": "Top – Apple, Citrus / Heart – Floral / Base – Sweet, Woody", "category": ["Fruity", "Woody", "Fresh"]},
    {"name": "Lattafa Raneen", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Fruity, Sweet / Heart – Floral / Base – Vanilla, Musk", "category": ["Floral", "Fruity", "Sweet"]},
    {"name": "Lattafa Rave Now (for Women)", "brand": "Lattafa", "gender": "Female", "season": "Spring, Fall", "notes": "Top – Red Fruits, Orange / Heart – Marshmallow, Jasmine, Lily of the Valley / Base – Vanilla, Musk, Moss", "category": ["Fruity", "Gourmand", "Floral"]},
    {"name": "Lattafa Rave Now Intense", "brand": "Lattafa", "gender": "Male/Unisex", "season": "Spring, Fall", "notes": "Top – Cucumber, Watermelon, Tangerine / Heart – Basil, Sage / Base – Sandalwood, Leather, Cedar", "category": ["Fresh", "Woody", "Aromatic"]},
    {"name": "Lattafa Sakeena", "brand": "Lattafa", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top – Passionfruit, Mandarin Orange, Ozonic Notes / Heart – Raspberry, Rose, Orange Blossom, Sea Salt / Base – Toffee, Praline, Vanilla, Musk", "category": ["Fruity", "Gourmand", "Floral"]},
    {"name": "Lattafa Teriaq", "brand": "Lattafa", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top – Caramel, Bitter Almond, Apricot, Pink Pepper / Heart – Honey, Rhubarb, White Flowers, Rose / Base – Leather, Vanilla, Musk, Vetiver, Labdanum", "category": ["Gourmand", "Floral", "Oriental"]},
    {"name": "Lattafa Teriaq Intense", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Saffron, Bergamot / Heart – Plum Liquor, Cinnamon / Base – Amber, Tonka Bean, Benzoin", "category": ["Oriental", "Spicy", "Sweet"]},
    {"name": "Lattafa Vanilla Freak (Give Me Gourmand)", "brand": "Lattafa", "gender": "Unisex / Female-leaning", "season": "Fall, Spring", "notes": "Top – Cupcake / Heart – Sugar Frosting, Almond, Cinnamon / Base – Butter, Vanilla, Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Lattafa Whipped Pleasure (Give Me Gourmand)", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Caramel, Popcorn, Salted Caramel / Heart – Milk, Jasmine / Base – Tonka, Benzoin, Musk, Ambrofix", "category": ["Gourmand", "Sweet"]},
    {"name": "Lattafa Yara Candy Body Spray", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Candy, Sweet / Heart – Fruity / Base – Vanilla, Musk", "category": ["Gourmand", "Sweet", "Fruity"]},
    {"name": "Lattafa Yara Tous", "brand": "Lattafa", "gender": "Female", "season": "Versatile", "notes": "Top – Fruity, Sweet / Heart – Floral / Base – Vanilla, Musk", "category": ["Floral", "Fruity", "Sweet"]},
    {"name": "Love & Peace", "brand": "Lattafa", "gender": "Unisex/Female", "season": "Spring–Fall", "notes": "Soft floral, musky, or peaceful sweet", "category": ["Floral", "Sweet"]},
    {"name": "Maison Alhambra Luxe Chic", "brand": "Maison Alhambra", "gender": "Female/Unisex", "season": "Spring, Fall", "notes": "Top – Tangerine, Freesia / Heart – Lily of the Valley, Jasmine, Rose / Base – Musk, Sandalwood, Amber", "category": ["Floral", "Fresh"]},
    {"name": "Maison Asrar Vanilla Aura", "brand": "Maison Asrar", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top – Vanilla / Heart – Creamy Sweet / Base – Vanilla, Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Maison Asrar Vanilla Seduction", "brand": "Maison Asrar", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top – Plum, Jasmine, Lily of the Valley / Heart – Vanilla, Brown Sugar, Caramel / Base – Tonka, Patchouli, Amber, Musk", "category": ["Gourmand", "Floral", "Sweet"]},
    {"name": "Majestic Supreme", "brand": "Le Falcone", "gender": "Women/Unisex", "season": "Fall–Winter / versatile", "notes": "Top – Rose, peony, pink pepper / Heart – Raspberry blossom, jasmine / Base – Amber, papyrus, tonka, vanilla", "category": ["Floral", "Sweet"]},
    {"name": "Malika", "brand": "Nusuk", "gender": "Female", "season": "Versatile", "notes": "Floral or oriental", "category": ["Floral", "Oriental"]},
    {"name": "Mango Affogato", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Spring–Summer / year-round", "notes": "Top – Mango, nutmeg, clove / Heart – Leather, saffron, amber, moss / Base – Akigalawood, patchouli, vetiver, cypriol", "category": ["Fruity", "Woody", "Spicy"]},
    {"name": "Mango Ice", "brand": "Gulf Orchid", "gender": "Unisex", "season": "Spring–Summer", "notes": "Fruity mango with cool/icy facets", "category": ["Fruity", "Fresh"]},
    {"name": "Mayar", "brand": "Lattafa", "gender": "Female", "season": "Spring, Summer", "notes": "Top – Lychee, Raspberry, Violet Leaf / Heart – Peony, White Rose, Jasmine / Base – Musk, Vanilla", "category": ["Floral", "Fruity", "Fresh"]},
    {"name": "Mayar Natural Intense Body Spray", "brand": "Mayar", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Sweet Gourmand / Heart – Vanilla / Base – Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Melt Cafe Bliss", "brand": "Mamlakat Al Oud / Fragrance World", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Black Coffee, Amaretto Liquor / Heart – Vanilla Ice Cream, Speculoos / Base – Vanilla Pods, Brown Sugar, Grey Amber", "category": ["Gourmand", "Sweet"]},
    {"name": "Melt Crème Caramel", "brand": "Mamlakat Al Oud", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top – Caramel, Vanilla Flower / Heart – Dulce de Leche, Cotton Candy, Frangipani, White Flowers / Base – Vanilla Pod, Tonka Bean, Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Melt Marshmallows Kiss", "brand": "Mamlakat Al Oud", "gender": "Unisex", "season": "Fall, Winter, Spring", "notes": "Top – Strawberry, Blackberry (or Caramel/Milk) / Heart – Jasmine, Rose, Marshmallow, Vanilla, Honey / Base – Vanilla, Musk, Praline, Tonka", "category": ["Gourmand", "Floral", "Sweet"]},
    {"name": "Melt Vanilla Madness", "brand": "Mamlakat Al Oud", "gender": "Unisex (leans feminine)", "season": "Fall, Winter (versatile year-round)", "notes": "Top – Vanilla (woody tones), Lavender, Cacao, Ginger / Heart – Vanilla Caviar / Base – Vanilla Absolute", "category": ["Gourmand", "Sweet"]},
    {"name": "Melt Velvet Breeze", "brand": "Mamlakat Al Oud", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Italian Bergamot, Pistachio Gelato, Hazelnut, Sweet Rum, Cardamom / Heart – Geranium, White Peony, Muguet, Jasmine / Base – Amber, Musk, Woody Notes", "category": ["Gourmand", "Floral", "Woody"]},
    {"name": "Miss Armaf Mystique", "brand": "Armaf", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Pear, Tangerine, Bergamot, Orange / Heart – Vanilla, Strawberry, Mimosa, Rose, Ylang Ylang, Jasmine, Passionfruit / Base – Vanilla, Coffee, Tonka Bean, Patchouli, Vetiver", "category": ["Floral", "Fruity", "Gourmand"]},
    {"name": "Momento", "brand": "Riiffs", "gender": "Unisex", "season": "Versatile", "notes": "Soft or aromatic (limited public data)", "category": ["Aromatic"]},
    {"name": "Mystique Charm", "brand": "Mystique Charm", "gender": "Unisex/Female", "season": "Cooler seasons", "notes": "Mysterious oriental or floral-woody", "category": ["Oriental", "Floral", "Woody"]},
    {"name": "Nagham", "brand": "Atyaab", "gender": "Unisex possible", "season": "Versatile", "notes": "Arabic-style (floral-woody or oriental)", "category": ["Floral", "Woody", "Oriental"]},
    {"name": "Nusuk Falak", "brand": "Nusuk", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Brown Sugar, Caramel, Biscuit / Heart – Toffee, Vanilla Bean, Amber / Base – White Musk, Praline", "category": ["Gourmand", "Sweet"]},
    {"name": "Obsidian", "brand": "French Avenue", "gender": "Unisex/Male", "season": "Fall–Winter", "notes": "Dark, woody, or smoky-oriental", "category": ["Woody", "Oriental", "Smoky"]},
    {"name": "Panache Angel Dust", "brand": "Khadlaj", "gender": "Female", "season": "Spring–Fall / versatile", "notes": "Soft, powdery, musk-vanilla / “angelic”", "category": ["Floral", "Sweet", "Powdery"]},
    {"name": "Paris Corner Eshal Vanilla", "brand": "Paris Corner", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top – Sugar, Sweet Notes / Heart – Rose, Jasmine / Base – Vanilla, Caramel, Musk", "category": ["Gourmand", "Floral", "Sweet"]},
    {"name": "Paris Corner Khair Men", "brand": "Paris Corner", "gender": "Male/Unisex", "season": "Fall, Winter", "notes": "Top – Davana, Bergamot, Pink Pepper / Heart – Agarwood (Oud), Amber, Rosemary / Base – Leather, Vetiver, Musk", "category": ["Woody", "Oud", "Spicy"]},
    {"name": "Paris Corner Marshmallow Blush", "brand": "Paris Corner", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top – Marshmallow, Sweet / Heart – Fruity / Base – Vanilla, Musk", "category": ["Gourmand", "Sweet", "Fruity"]},
    {"name": "Paris Corner Qissa Delicious", "brand": "Paris Corner", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Whipped Cream, Dark Chocolate, Orange / Heart – Marshmallow, Coconut, Jasmine / Base – Vanilla, White Musk", "category": ["Gourmand", "Sweet"]},
    {"name": "Pecan Butter Cookie", "brand": "Arabiyat Sugar", "gender": "Unisex/Female", "season": "Fall–Winter", "notes": "Top – Pecan, coconut milk, butter / Heart – Hazelnut, almond, roasted nuts / Base – Hazelnut, vanilla, ambergris", "category": ["Gourmand", "Sweet"]},
    {"name": "Phlur Heavy Cream", "brand": "Phlur", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Marshmallow, Sugar, Citrus / Heart – Coconut, Jasmine / Base – Whipped Cream, Vanilla, Caramel", "category": ["Gourmand", "Sweet"]},
    {"name": "Phlur Vanilla Skin", "brand": "Phlur", "gender": "Unisex (female-leaning)", "season": "Fall, Winter", "notes": "Top – Sugar, Pink Pepper, Apple / Heart – Cashmere Wood, Jasmine, Lily / Base – Vanilla, Sandalwood, Agarwood, Benzoin", "category": ["Gourmand", "Woody", "Sweet"]},
    {"name": "Pink Velvet", "brand": "Maison Alhambra", "gender": "Female", "season": "Spring–Fall", "notes": "Soft, powdery, rosy, or gourmand-pink", "category": ["Floral", "Sweet", "Powdery"]},
    {"name": "Pink Yara / Yara Pink", "brand": "Lattafa", "gender": "Female", "season": "Spring–Summer", "notes": "Top – Orchid, heliotrope, tangerine / Heart – Gourmand accord, tropical fruits / Base – Vanilla, musk, sandalwood", "category": ["Floral", "Gourmand", "Fruity"]},
    {"name": "Raheeq", "brand": "Nusuk", "gender": "Female/Unisex", "season": "Versatile", "notes": "Soft, sweet, or floral", "category": ["Floral", "Sweet"]},
    {"name": "Rave Rage", "brand": "Lattafa", "gender": "Unisex (leans masculine)", "season": "Year-round", "notes": "Top – Apple, mint / Heart – Geranium, cinnamon, lavender / Base – Vanilla, Peru balsam, cedarwood, guaiac wood", "category": ["Fresh", "Woody", "Spicy"]},
    {"name": "Rasasi Hawas Diva", "brand": "Rasasi", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Red Fruits, Rhubarb, Lychee / Heart – Rose, Frankincense, Cedar / Base – Vanilla, Musk, Ambergris", "category": ["Fruity", "Floral", "Woody"]},
    {"name": "Rasasi Hawas Eclat (Eclat Hawas)", "brand": "Rasasi", "gender": "Female", "season": "Spring, Fall", "notes": "Top – Litchi/Lychee, Bergamot, Pear, Pistachio / Heart – Rose, Incense / Base – Vanilla, Amber, Musk, Woody Notes", "category": ["Fruity", "Floral", "Woody"]},
    {"name": "Rasasi Hawas Ice", "brand": "Rasasi", "gender": "Male", "season": "Versatile", "notes": "Top – Apple, Italian Lemon, Sicilian Bergamot, Star Anise / Heart – Plum, Orange Blossom, Cardamom / Base – Musk, Moss, Driftwood, Amber", "category": ["Fresh", "Fruity", "Aromatic"]},
    {"name": "Rasasi Hawas London", "brand": "Rasasi", "gender": "Unisex", "season": "Fall, Spring", "notes": "Top – Pink Pepper, Saffron, Pear / Heart – Rose, Frankincense, White Flowers / Base – Blonde Woods, Vanilla, Amber, Musk", "category": ["Floral", "Woody", "Spicy"]},
    {"name": "Rasasi Hawas Pink", "brand": "Rasasi", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Cinnamon, Nutmeg, Neroli / Heart – Marshmallow, Tuberose, Orange Blossom / Base – Cotton Candy, Vanilla, Tonka Bean", "category": ["Gourmand", "Floral", "Sweet"]},
    {"name": "Red Velvet", "brand": "Armaf Delights", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top – Strawberry, Lemon / Heart – Whipped Sugar, Sugarberry, Frangipani / Base – Vanilla Bean, Musk, Amber", "category": ["Gourmand", "Fruity", "Sweet"]},
    {"name": "Rizz Tiramisu Candy", "brand": "Rizz", "gender": "Female", "season": "Spring, Fall", "notes": "Top – Bergamot / Heart – Blackcurrant, Strawberry Milk / Base – Musk, Vanilla", "category": ["Gourmand", "Fruity", "Sweet"]},
    {"name": "Safa by Nusuk", "brand": "Nusuk", "gender": "Unisex/Female", "season": "Spring–Summer / versatile", "notes": "Top – Marshmallow, Strawberry, Lemon / Heart – Coconut, Sugar, Nectarine / Base – Vanilla, Musk, Ambroxan", "category": ["Gourmand", "Fruity", "Sweet"]},
    {"name": "Sahari Ghubar Al Dhahab", "brand": "Sahari", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Cinnamon, Pear, Mandarin, Floral notes / Heart – Jasmine Sambac, Orange Blossom / Base – White Musk, Vanilla, Tonka Bean, Coffee, Patchouli", "category": ["Floral", "Spicy", "Sweet"]},
    {"name": "Samiya", "brand": "Khadlaj", "gender": "Female", "season": "Versatile", "notes": "Floral or oriental", "category": ["Floral", "Oriental"]},
    {"name": "Sara Debai Essences", "brand": "Sara Debai", "gender": "Female", "season": "Spring–Summer", "notes": "Top – Heliotrope, orchid, tangerine / Heart – Gourmand accord, tropical fruits / Base – Vanilla, musk, sandalwood", "category": ["Floral", "Gourmand", "Fruity"]},
    {"name": "Spectre / Sceptre Malachite", "brand": "Maison Alhambra", "gender": "Unisex", "season": "Spring–Summer", "notes": "Top – Green tangerine, bergamot, blackcurrant / Heart – Aromatic + spicy notes, lavender, pink pepper, jasmine / Base – Amber, musk, woody notes, vetiver", "category": ["Fresh", "Aromatic", "Woody"]},
    {"name": "Strawberry Tres Leches", "brand": "Arabiyat Sugar", "gender": "Female", "season": "Spring–Summer / year-round", "notes": "Strawberry + milky cake gourmand", "category": ["Gourmand", "Fruity", "Sweet"]},
    {"name": "Sugar Crown", "brand": "Lattafa", "gender": "Female/Unisex", "season": "Fall–Winter", "notes": "Sweet/sugar gourmand", "category": ["Gourmand", "Sweet"]},
    {"name": "Sugar Me Dulce de Leche", "brand": "Maison Alhambra", "gender": "Unisex/Female", "season": "Fall–Winter", "notes": "Dulce de leche / caramel-vanilla gourmand", "category": ["Gourmand", "Sweet"]},
    {"name": "Sweet Surrender", "brand": "Mahajan", "gender": "Female", "season": "Fall–Winter / versatile", "notes": "Soft sweet/gourmand", "category": ["Gourmand", "Sweet"]},
    {"name": "Sweet Surrender Pink Parfait", "brand": "Mahajan", "gender": "Female", "season": "Spring–Summer / year-round", "notes": "Pink/fruity-parfait sweet", "category": ["Gourmand", "Fruity", "Sweet"]},
    {"name": "Tahira", "brand": "Riiffs", "gender": "Female", "season": "Versatile", "notes": "Likely floral or oriental (limited public data)", "category": ["Floral", "Oriental"]},
    {"name": "Taif", "brand": "Riiffs", "gender": "Unisex", "season": "Versatile (Spring–Summer preferred)", "notes": "Top – Ginger, Calabrian Bergamot, Lemon, Orange Blossom / Heart – Musk, Rose Petals, Tuberose / Base – Vanilla Bean, Amberwood, Clearwood", "category": ["Floral", "Fresh", "Woody"]},
    {"name": "The King", "brand": "Ali", "gender": "Male", "season": "Fall–Winter / versatile", "notes": "Masculine woody or oriental", "category": ["Woody", "Oriental"]},
    {"name": "Toffee Ganache", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Fall–Winter", "notes": "Toffee/chocolate gourmand", "category": ["Gourmand", "Sweet"]},
    {"name": "Valentine Milano", "brand": "Valentine", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top – Raspberry, Peach, Bergamot / Heart – Rose, Jasmine, Orange Blossom / Base – Vanilla, Amber, Woods", "category": ["Floral", "Fruity", "Sweet"]},
    {"name": "Valentine Nero Xtravagant", "brand": "Valentine (Urban Collection)", "gender": "Male / Unisex (leans masculine)", "season": "Fall, Winter (versatile)", "notes": "Top – Calabrian Bergamot, Espresso Coffee Accord / Heart – Coffee / Base – Vetiver", "category": ["Woody", "Fresh", "Aromatic"]},
    {"name": "Vanilla Addiction", "brand": "Gulf Orchid", "gender": "Unisex/Female", "season": "Fall–Winter", "notes": "Vanilla-forward gourmand", "category": ["Gourmand", "Sweet"]},
    {"name": "Vanilla Dunes", "brand": "Khadlaj", "gender": "Unisex", "season": "Autumn, Winter", "notes": "Top – Vanilla, Cinnamon, Cardamom, Bergamot / Heart – Orange Blossom, Guaiac Wood, Bourbon / Base – Praline, Amber, Musk", "category": ["Gourmand", "Spicy", "Woody"]},
    {"name": "Yara Elixir", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter, Cool Spring Days", "notes": "Top – Strawberry S'mores, Black Currant / Heart – Jasmine, Orange Blossom / Base – Vanilla, Caramel, Amber, Musk", "category": ["Gourmand", "Floral", "Sweet"]},
    {"name": "Zenith", "brand": "Riiffs", "gender": "Unisex", "season": "Spring–Summer / versatile", "notes": "Top – Coconut, Vanilla, Cream / Heart – Rum, Saffron / Base – Cashmeran, Tonka Bean", "category": ["Gourmand", "Sweet", "Fresh"]},
    {"name": "Zimaya Fatima (Fatima Pink)", "brand": "Zimaya", "gender": "Female", "season": "Spring, Fall", "notes": "Top – Rhubarb, Bergamot, Grapefruit, Nutmeg / Heart – Rose, Jasmine / Base – Musk, Vanilla, Vetiver, Ambergris", "category": ["Floral", "Fruity", "Fresh"]},
    {"name": "Zimaya Hawwa Red", "brand": "Zimaya", "gender": "Female", "season": "Fall, Winter", "notes": "Top – Cassis, Strawberry, Raspberry, Orange / Heart – Black Currant, Grapefruit, Peach, Lily / Base – Musk, Vanilla, Patchouli", "category": ["Fruity", "Floral", "Sweet"]},
]


# ====================== GENDER HELPERS ======================

def normalize_gender(g: str) -> str:
    g = g.lower().strip()
    if re.search(r"\bfemale[- ]?leaning\b|\bleans feminine\b|\bleans female\b", g):
        return "Female-leaning"
    if re.search(r"\bmale[- ]?leaning\b|\bleans masculine\b|\bleans male\b", g):
        return "Male-leaning"
    if g in ["unisex/male", "male/unisex", "male / unisex"]:
        return "Male-leaning"
    if g in ["unisex/female", "female/unisex", "women/unisex", "unisex / female-leaning"]:
        return "Female-leaning"
    if g == "male":
        return "Male"
    if g in ["female", "women"]:
        return "Female"
    return "Unisex"


def matches_gender(fragrance: Dict, preferred: str) -> bool:
    """
    - Male   → Male + Male-leaning + Unisex
    - Female → Female + Female-leaning + Unisex
    - Unisex → pure Unisex + leanings
    - Any    → everything
    """
    if preferred == "Any":
        return True
    fg = normalize_gender(fragrance["gender"])
    if preferred == "Male":
        return fg in ["Male", "Male-leaning", "Unisex"]
    if preferred == "Female":
        return fg in ["Female", "Female-leaning", "Unisex"]
    if preferred == "Unisex":
        return fg in ["Unisex", "Male-leaning", "Female-leaning"]
    return True


# ====================== OTHER MATCHERS ======================

def matches_weather(fragrance: Dict, weather: str) -> bool:
    season = fragrance["season"].lower()
    if weather == "Any":
        return True
    if weather == "Hot / Summer":
        return any(x in season for x in ["spring", "summer", "versatile", "year-round"])
    if weather == "Warm / Mild":
        return any(x in season for x in ["spring", "fall", "autumn", "versatile", "year-round", "mild"])
    if weather == "Cool / Autumn":
        return any(x in season for x in ["fall", "autumn", "winter", "cooler", "versatile", "year-round"])
    if weather == "Cold / Winter":
        return any(x in season for x in ["fall", "winter", "cooler", "autumn", "versatile"])
    return True


def matches_category(fragrance: Dict, category: str) -> bool:
    if category == "Any":
        return True
    return category in fragrance["category"]


def matches_occasion(fragrance: Dict, occasion: str) -> bool:
    if occasion == "Any":
        return True
    season = fragrance["season"].lower()
    cats = fragrance["category"]
    if occasion == "Daily / Casual":
        return True
    if occasion == "Work / Office":
        return not ("Gourmand" in cats and ("winter" in season or "fall" in season))
    if occasion == "Date / Evening":
        return any(c in cats for c in ["Oriental", "Gourmand", "Woody", "Spicy", "Leather", "Oud"])
    if occasion == "Formal / Event":
        return any(c in cats for c in ["Oriental", "Woody", "Floral", "Oud"])
    if occasion == "Outdoor / Sporty":
        return any(c in cats for c in ["Fresh", "Citrus", "Aromatic", "Fruity"])
    return True


# ====================== SCORING & TOP N ======================

def score_fragrance(f: Dict, gender: str, weather: str, category: str, occasion: str) -> int:
    score = 0
    season = f["season"].lower()
    cats = f["category"]
    g = normalize_gender(f["gender"])

    # Gender
    if gender == "Any":
        score += 5
    elif gender == "Male":
        if g == "Male": score += 15
        elif g == "Male-leaning": score += 12
        elif g == "Unisex": score += 8
    elif gender == "Female":
        if g == "Female": score += 15
        elif g == "Female-leaning": score += 12
        elif g == "Unisex": score += 8
    elif gender == "Unisex":
        if g == "Unisex": score += 15
        else: score += 8

    # Weather
    if weather == "Any":
        score += 5
    elif weather == "Hot / Summer":
        if "summer" in season: score += 15
        elif any(x in season for x in ["spring", "versatile", "year-round"]): score += 10
    elif weather == "Warm / Mild":
        if any(x in season for x in ["spring", "fall", "autumn", "mild"]): score += 15
        elif any(x in season for x in ["versatile", "year-round"]): score += 12
    elif weather == "Cool / Autumn":
        if any(x in season for x in ["fall", "autumn"]): score += 15
        elif any(x in season for x in ["winter", "cooler"]): score += 12
    elif weather == "Cold / Winter":
        if "winter" in season: score += 15
        elif any(x in season for x in ["fall", "autumn", "cooler"]): score += 12

    # Category
    if category == "Any":
        score += 5
    elif category in cats:
        score += 15
        if cats and cats[0] == category:
            score += 5

    # Occasion
    if occasion == "Any":
        score += 5
    elif occasion == "Daily / Casual":
        score += 8
    elif occasion == "Work / Office":
        score += 10 if not ("Gourmand" in cats and ("winter" in season or "fall" in season)) else 3
    elif occasion == "Date / Evening":
        score += 15 if any(c in cats for c in ["Oriental", "Gourmand", "Woody", "Spicy", "Leather", "Oud"]) else 5
    elif occasion == "Formal / Event":
        score += 15 if any(c in cats for c in ["Oriental", "Woody", "Floral", "Oud"]) else 5
    elif occasion == "Outdoor / Sporty":
        score += 15 if any(c in cats for c in ["Fresh", "Citrus", "Aromatic", "Fruity"]) else 4

    score += random.randint(0, 3)
    return score


def get_top_fragrances(gender: str, weather: str, category: str, occasion: str, top_n: int) -> List[Dict]:
    scored = []
    for f in FRAGRANCES:
        if (matches_gender(f, gender) and matches_weather(f, weather) and
            matches_category(f, category) and matches_occasion(f, occasion)):
            s = score_fragrance(f, gender, weather, category, occasion)
            scored.append((s, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for score, f in scored[:top_n]]


# ====================== LAYERING LOGIC ======================

# Complementary category pairs that generally layer well
GOOD_LAYER_PAIRS = [
    ("Gourmand", "Fresh"),
    ("Gourmand", "Floral"),
    ("Gourmand", "Woody"),
    ("Gourmand", "Fruity"),
    ("Sweet", "Fresh"),
    ("Sweet", "Woody"),
    ("Floral", "Woody"),
    ("Floral", "Oriental"),
    ("Fruity", "Woody"),
    ("Fruity", "Fresh"),
    ("Oriental", "Floral"),
    ("Oriental", "Woody"),
    ("Spicy", "Sweet"),
    ("Spicy", "Woody"),
    ("Citrus", "Gourmand"),
    ("Citrus", "Floral"),
    ("Aromatic", "Gourmand"),
    ("Oud", "Floral"),
    ("Oud", "Sweet"),
]

def layer_score(f1: Dict, f2: Dict) -> int:
    """How well two fragrances layer together."""
    if f1["name"] == f2["name"]:
        return -100
    cats1 = set(f1["category"])
    cats2 = set(f2["category"])
    score = 0

    # Complementary categories
    for a, b in GOOD_LAYER_PAIRS:
        if (a in cats1 and b in cats2) or (b in cats1 and a in cats2):
            score += 12

    # Same family can also work (e.g. two gourmands) but lower
    if cats1 & cats2:
        score += 4

    # Prefer different intensity / season balance
    s1 = f1["season"].lower()
    s2 = f2["season"].lower()
    if ("summer" in s1 or "spring" in s1) and ("winter" in s2 or "fall" in s2):
        score += 6
    if ("winter" in s1 or "fall" in s1) and ("summer" in s2 or "spring" in s2):
        score += 6

    score += random.randint(0, 4)
    return score


def suggest_layering_combos(pool: List[Dict], num_combos: int = 3) -> List[Tuple[Dict, Dict, str]]:
    """Return list of (frag1, frag2, reason) tuples."""
    if len(pool) < 2:
        return []

    candidates = []
    for i, f1 in enumerate(pool):
        for f2 in pool[i+1:]:
            s = layer_score(f1, f2)
            if s > 8:  # only decent pairs
                reason = build_layer_reason(f1, f2)
                candidates.append((s, f1, f2, reason))

    candidates.sort(key=lambda x: x[0], reverse=True)

    # Pick top unique combos (avoid repeating the same fragrance too much)
    used = set()
    results = []
    for s, f1, f2, reason in candidates:
        key1, key2 = f1["name"], f2["name"]
        if key1 in used and key2 in used:
            continue
        results.append((f1, f2, reason))
        used.add(key1)
        used.add(key2)
        if len(results) >= num_combos:
            break

    return results


def build_layer_reason(f1: Dict, f2: Dict) -> str:
    c1 = ", ".join(f1["category"][:2])
    c2 = ", ".join(f2["category"][:2])
    return f"{c1} + {c2}"


# ====================== DISPLAY ======================

def display_fragrance(f: Dict, idx: int = None, is_top1: bool = False):
    if is_top1:
        prefix = "★ TOP PICK  "
    elif idx:
        prefix = f"#{idx}  "
    else:
        prefix = "• "
    print(f"{prefix}{f['name']} – {f['brand']}")
    print(f"   Gender: {f['gender']} | Season: {f['season']}")
    print(f"   Category: {', '.join(f['category'])}")
    print(f"   Notes: {f['notes']}")
    print()


def display_combo(f1: Dict, f2: Dict, reason: str, idx: int):
    print(f"#{idx}  LAYERING COMBO")
    print(f"   Base / First : {f1['name']} – {f1['brand']}")
    print(f"   Layer / Top  : {f2['name']} – {f2['brand']}")
    print(f"   Why it works : {reason}")
    print(f"   Tip          : Spray the richer/heavier one first, then the lighter one on top.")
    print()


# ====================== MAIN ======================

def main():
    print("=" * 65)
    print("   FRAGRANCE GENERATOR + LAYERING COMBO SUGGESTER")
    print("=" * 65)
    print()

    # Gender
    print("1. Gender preference:")
    print("   1) Male          (Male + Male-leaning + Unisex)")
    print("   2) Female        (Female + Female-leaning + Unisex)")
    print("   3) Unisex        (pure Unisex + leanings)")
    print("   4) Any")
    g_choice = input("   Enter choice (1-4): ").strip()
    gender_map = {"1": "Male", "2": "Female", "3": "Unisex", "4": "Any"}
    gender = gender_map.get(g_choice, "Any")

    # Weather
    print("\n2. Current weather / season:")
    print("   1) Hot / Summer")
    print("   2) Warm / Mild")
    print("   3) Cool / Autumn")
    print("   4) Cold / Winter")
    print("   5) Any")
    w_choice = input("   Enter choice (1-5): ").strip()
    weather_map = {"1": "Hot / Summer", "2": "Warm / Mild", "3": "Cool / Autumn", "4": "Cold / Winter", "5": "Any"}
    weather = weather_map.get(w_choice, "Any")

    # Category
    print("\n3. Preferred category:")
    print("   1) Gourmand / Sweet")
    print("   2) Floral")
    print("   3) Woody")
    print("   4) Oriental / Spicy")
    print("   5) Fresh / Citrus / Aromatic")
    print("   6) Fruity")
    print("   7) Any")
    c_choice = input("   Enter choice (1-7): ").strip()
    category_map = {"1": "Gourmand", "2": "Floral", "3": "Woody", "4": "Oriental", "5": "Fresh", "6": "Fruity", "7": "Any"}
    category = category_map.get(c_choice, "Any")

    # Occasion
    print("\n4. Place / Occasion:")
    print("   1) Daily / Casual")
    print("   2) Work / Office")
    print("   3) Date / Evening")
    print("   4) Formal / Event")
    print("   5) Outdoor / Sporty")
    print("   6) Any")
    o_choice = input("   Enter choice (1-6): ").strip()
    occasion_map = {"1": "Daily / Casual", "2": "Work / Office", "3": "Date / Evening", "4": "Formal / Event", "5": "Outdoor / Sporty", "6": "Any"}
    occasion = occasion_map.get(o_choice, "Any")

    # Number of single recommendations
    print("\n5. How many single fragrance recommendations?")
    print("   1) Top 1")
    print("   2) Top 3")
    print("   3) Top 5")
    n_choice = input("   Enter choice (1-3): ").strip()
    num_map = {"1": 1, "2": 3, "3": 5}
    num = num_map.get(n_choice, 3)

    # Get ranked singles
    selected = get_top_fragrances(gender, weather, category, occasion, num)

    print("\n" + "=" * 65)
    print(f"Filters → Gender: {gender} | Weather: {weather}")
    print(f"          Category: {category} | Occasion: {occasion}")
    print("=" * 65)

    if not selected:
        print("\nNo fragrances matched your filters. Try selecting 'Any' for some options.")
        return

    title = {1: "TOP 1 PICK OF THE DAY", 3: "TOP 3 PICKS OF THE DAY", 5: "TOP 5 PICKS OF THE DAY"}
    print(f"\n{title.get(num, 'TOP PICKS')}\n")

    for i, f in enumerate(selected, 1):
        display_fragrance(f, i, is_top1=(i == 1))

    # Layering suggestions
    # Use a larger pool for better combo variety
    pool = get_top_fragrances(gender, weather, category, occasion, min(25, len(FRAGRANCES)))
    combos = suggest_layering_combos(pool, num_combos=3)

    if combos:
        print("-" * 65)
        print("LAYERING COMBOS FOR YOU")
        print("-" * 65)
        print()
        for i, (f1, f2, reason) in enumerate(combos, 1):
            display_combo(f1, f2, reason, i)
    else:
        print("\n(Not enough matching fragrances to suggest layering combos.)")

    print("-" * 65)
    again = input("Generate new recommendations with same filters? (y/n): ").strip().lower()
    if again == "y":
        selected = get_top_fragrances(gender, weather, category, occasion, num)
        print(f"\n{title.get(num, 'TOP PICKS')}\n")
        for i, f in enumerate(selected, 1):
            display_fragrance(f, i, is_top1=(i == 1))

        pool = get_top_fragrances(gender, weather, category, occasion, min(25, len(FRAGRANCES)))
        combos = suggest_layering_combos(pool, num_combos=3)
        if combos:
            print("-" * 65)
            print("NEW LAYERING COMBOS")
            print("-" * 65 + "\n")
            for i, (f1, f2, reason) in enumerate(combos, 1):
                display_combo(f1, f2, reason, i)


if __name__ == "__main__":
    main()
