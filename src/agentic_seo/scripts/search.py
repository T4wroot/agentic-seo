import csv
import json
import os
import argparse

def load_csv(filename):
    filepath = os.path.join(os.path.dirname(__file__), '..', 'data', filename)
    data = []
    with open(filepath, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)
    return data

def search_rules(industry=None):
    rules = load_csv('rules.csv')
    if industry:
        return [r for r in rules if r['industry'].lower() == industry.lower()]
    return rules

def search_frameworks(framework=None):
    frameworks = load_csv('frameworks.csv')
    if framework:
        return [f for f in frameworks if f['framework'].lower() == framework.lower()]
    return frameworks

def search_anti_patterns():
    return load_csv('anti_patterns.csv')

def main():
    parser = argparse.ArgumentParser(description='SEO Pro Max Search Engine')
    parser.add_argument('--industry', type=str, help='Filter rules by industry')
    parser.add_argument('--framework', type=str, help='Filter principles by framework')
    parser.add_argument('--anti-patterns', action='store_true', help='List anti-patterns')
    
    args = parser.parse_args()
    
    result = {}
    
    if args.anti_patterns:
        result['anti_patterns'] = search_anti_patterns()
    
    if args.framework:
        result['frameworks'] = search_frameworks(args.framework)
        
    if args.industry:
        result['rules'] = search_rules(args.industry)
        
    if not args.anti_patterns and not args.framework and not args.industry:
        # If no specific flags, return everything
        result['rules'] = search_rules()
        result['frameworks'] = search_frameworks()
        result['anti_patterns'] = search_anti_patterns()
        
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
