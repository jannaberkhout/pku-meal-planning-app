from dataclasses import dataclass

@dataclass
class Ingredient:
    name: str

@dataclass
class Recipe:
    name: str
    ingredients: list[Ingredient]
    protein: float
    calories: float

    def __repr__(self):
        ratio = self.protein / self.calories if self.calories > 0 else 0
        
        return (f"Recipe(name='{self.name}', "
                f"ingredients={len(self.ingredients)}, "
                f"P/C Ratio: {ratio:.2f})")
