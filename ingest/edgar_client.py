from edgar import Company, set_identity

def get_two_aapl_10ks():
    set_identity("Tegan Dowd teganreef.d@gmail.com")

    company = Company("AAPL")
    filings = company.get_filings(form="10-K")

    filing_1 = filings[0]
    filing_2 = filings[1]

    print("Filing 1:", filing_1)
    print("Filing 2:", filing_2)

    return filing_1, filing_2







if __name__ == "__main__":
    filing_1, filing_2 = get_two_aapl_10ks()

    tenk_1 = filing_1.obj()
    tenk_2 = filing_2.obj()

    risk_factors_1 = tenk_1.risk_factors
    risk_factors_2 = tenk_2.risk_factors

    print("Risk factors 1 length:", len(risk_factors_1))
    print("Risk factors 2 length:", len(risk_factors_2))

    with open("tests/fixtures/aapl_10k_2025_risk_factors.txt", "w") as f:
        f.write(risk_factors_1)

    with open("tests/fixtures/aapl_10k_2024_risk_factors.txt", "w") as f:
        f.write(risk_factors_2)

    print("Fixtures saved.")
    
    