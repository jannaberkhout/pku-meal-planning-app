from dataclasses import dataclass

@dataclass
class Ingredient:
    name: str

@dataclass
class Recipe:
    name: str
    ingredients: list[str]
    protein: float
    calories: float
    n_persons: int
    receptcat: str
    preptime: str
    instructions: str

    def __repr__(self):
        ratio = self.protein / self.calories if self.calories > 0 else 0
        
        return (f"Recipe(name='{self.name}', "
                f"preptime= {self.preptime} "
                f"persons(persons={self.n_persons}, "
                f"ingredients={len(self.ingredients)}, "
                f"instructions={len(self.instructions)}, "
                f"proteins={self.protein}, "
                f"calories={self.calories}, "
                f"receptcat={self.receptcat}, "
                f"P/C Ratio: {ratio:.2f})")
