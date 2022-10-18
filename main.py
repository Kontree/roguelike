import random
import time
from abc import ABC, abstractmethod


class Unit(ABC):
    name = ''

    def __init__(self, room: 'Room',
                 health: float,
                 damage: float,
                 defense: float = 0,
                 weapon: 'Weapon' = None,
                 helmet: 'Helmet' = None,
                 armor: 'Armor' = None,
                 boots: 'Boots' = None,
                 inventory: list = None):
        self.health = self.max_health = health
        if weapon:
            self.damage = damage + weapon.damage
            self.damage_spread = weapon.damage_spread
        else:
            self.damage = damage
            self.damage_spread = 0.1 # base amplitude of damage (0.9-1.1)
        self.defense = defense
        self.weapon = weapon
        self.helmet = helmet
        self.armor = armor
        self.boots = boots

        self.inventory = inventory if inventory else {}
        self.room = room

    @abstractmethod
    def kick_from_room(self):
        pass

    def is_alive(self):
        return self.health > 0

    def attack(self, other: 'Unit', output: bool = False):
        if self.weapon:
            damage = self.damage * (1 - self.weapon.damage_spread +
                                    2 * random.random() * self.weapon.damage_spread) - other.defense
        else:
            damage = self.damage * (1 - self.damage_spread +
                                    2 * random.random() * self.damage_spread) - other.defense
        if output:
            formatter = '{0:.2f}'
            print(f'''Health of {self.name} : {formatter.format(self.health)}
Health of {other.name} : {formatter.format(other.health)}
{self.name} attacks {other.name} and hits him with {formatter.format(damage)} damage''')
        other.health -= damage

    def fight(self, other: 'Unit', output: bool = False):
        while self.is_alive() and other.is_alive():
            self.attack(other, output)
            if not other.is_alive():
                break
            other.attack(self, output)
            if output:
                time.sleep(1)
        return (self, other) if self.is_alive() else (other, self)  # returning a tuple representing winner/loser

    def enter_a_room(self, room: 'Room'):
        self.room = room


class Enemy(Unit):

    def __init__(self, room: 'Room',
                 health: float,
                 damage: float,
                 defense: float = 0,
                 weapon: 'Weapon' = None,
                 helmet: 'Helmet' = None,
                 armor: 'Armor' = None,
                 boots: 'Boots' = None,
                 inventory: list = None):
        super().__init__(room=room, health=health, damage=damage,
                         defense=defense, weapon=weapon, helmet=helmet,
                         armor=armor, boots=boots, inventory=inventory)

    @abstractmethod
    def get_random_dying_phrase(self):
        pass

    def kick_from_room(self):
        self.room.enemies.remove(self)


class Skeleton(Enemy):
    name = 'Skeleton'
    dying_phrases = ['crumbles to the floor', 'shatters into bones',
                     'crumbling into pieces', 'crashes to the ground']

    def __init__(self, room: 'Room', health: float = 20., damage: float = 2., defense: float = 0.):
        super().__init__(room, health, damage, defense)

    def get_random_dying_phrase(self):
        return random.choice(self.dying_phrases)


class Ghost(Enemy):
    name = 'Ghost'
    dying_phrases = ['vanishes in the air', 'flies away screaming',
                     'breaks down into dust particles', 'dies leaving an imprint on the wall']

    def __init__(self, room: 'Room', health: float = 10., damage: float = 4., defense: float = 0.):
        super().__init__(room, health, damage, defense)

    def get_random_dying_phrase(self):
        return random.choice(self.dying_phrases)


ALL_ENEMY_TYPES = Enemy.__subclasses__()  # All enemy types through subclasses of a class Unit
ALL_ITEM_IDS= []


class Hero(Unit):

    def __init__(self, name: str,
                 health: float,
                 damage: float,
                 defense: float,
                 room: 'Room' = None,
                 weapon: 'Weapon' = None,
                 helmet: 'Helmet' = None,
                 armor: 'Armor' = None,
                 boots: 'Boots' = None,
                 inventory: list = None):
        super().__init__(room=room, health=health, damage=damage,
                         defense=defense, weapon=weapon, helmet=helmet,
                         armor=armor, boots=boots, inventory=inventory)
        self.name = name
        self.inventory_for_print = {}

    def update_inventory(self):
        inventory = list(set([item.item_name for item in self.inventory]))

        def count_items(item, lst):
            count = 0
            for obj in lst:
                if item == obj.item_name:
                    count += 1
            return count

        for item in inventory:
            self.inventory_for_print[count_items(item, self.inventory)] = item

    def equip(self, equipment: 'Equipment'):
        equipment.equip()

    def unequip(self, equipment: 'Equipment'):
        self.inventory[equipment.item_name] = equipment
        if type(equipment) == Weapon:
            self.weapon = None
        elif type(equipment) == Helmet:
            self.helmet = None
        elif type(equipment) == Armor:
            self.armor = None
        elif type(equipment) == Boots:
            self.boots = None

    def kick_from_room(self):
        print('Sadly, this is the moment when your adventure comes to an end...')
        print('Goodbye and better luck next time!')
        exit()


class Item(ABC):

    def __init__(self, item_name: str):
        self.item_id = random.randint(100000, 999999)
        while self.item_id in ALL_ITEM_IDS:
            self.item_id = random.randint(100000, 999999)
        self.item_name = item_name


class Consumable(Item, ABC):

    def __init__(self, item_name: str, owner: 'Hero' = None):
        super().__init__(item_name)
        self.owner = owner

    @abstractmethod
    def use(self):
        pass


class HealingItem(Consumable):

    def __init__(self, item_name: str, heal_amount: float, owner: 'Hero' = None):
        super().__init__(item_name)
        self.heal_amount = heal_amount
        self.owner = owner

    def use(self):
        amount_of_heal = (self.heal_amount if self.owner.max_health - self.owner.health > self.heal_amount
                          else self.owner.max_health - self.owner.health)
        self.owner.health += amount_of_heal
        del self


class Equipment(Item, ABC):

    def __init__(self, item_name: str, owner: 'Unit' = None):
        super().__init__(item_name)
        self.owner = owner

    @abstractmethod
    def equip(self):
        pass


class Weapon(Equipment):

    def __init__(self, item_name: str, damage_spread: float, damage: float, owner: 'Unit' = None):
        super().__init__(item_name, owner)
        self.damage_spread = damage_spread
        self.damage = damage

    def equip(self):
        if isinstance(self.owner, Hero):
            if self.owner.weapon:
                self.owner.unequip(self.owner.weapon)
            self.owner.weapon = self


class Helmet(Equipment):

    def __init__(self, item_name: str, owner: 'Unit' = None):
        super().__init__(item_name, owner)

    def equip(self):
        if isinstance(self.owner, Hero):
            if self.owner.helmet:
                self.owner.unequip(self.owner.helmet)
            self.owner.helmet = self


class Armor(Equipment):

    def __init__(self, item_name: str, owner: 'Unit' = None):
        super().__init__(item_name, owner)

    def equip(self):
        if isinstance(self.owner, Hero):
            if self.owner.armor:
                self.owner.unequip(self.owner.armor)
            self.owner.armor = self


class Boots(Equipment):

    def __init__(self, item_name: str, owner: 'Unit' = None):
        super().__init__(item_name, owner)

    def equip(self):
        if isinstance(self.owner, Hero):
            if self.owner.boots:
                self.owner.unequip(self.owner.boots)
            self.owner.boots = self


ALL_EQUIPMENT_TYPES = Equipment.__subclasses__()


class Room:

    def __init__(self, enemies: list = None, prev_room: 'Room' = None,
                 next_room: 'Room' = None, items: list = None):
        self.enemies = enemies
        self.prev_room = prev_room
        self.items = items
        self.next_room = next_room


def create_a_hero():
    name = input('Type your name in: ')
    points = 10
    health, health_grow = 100, 10
    damage, damage_grow = 5, 1
    defense, defense_grow = 0, 0.2
    while points > 0:
        print(f'You have {points} points left')
        print(f'You can invest them in your health(+{health_grow}), '
              f'damage(+{damage_grow}) or defense(+0.{defense_grow})')
        print(f'''Your current statistics:
    health : {health}
    damage : {damage}
    defense : {defense}''')

        choice = input('Please enter a stat you want to invest to: ')
        while choice not in ['h', 'dmg', 'def', 'health', 'damage', 'defense']:
            print('Your input was invalid, please try again(health(h)/damage(dmg)/defense(def))')
            choice = input('Please enter a stat you want to invest to: ')

        amount = input('Please enter amount of points you want to invest: ')
        while not amount.isdigit() or int(amount) <= 0:
            print('Your input was invalid, please try again in digits and greater than 0')
            amount = input('Please enter amount of points you want to invest: ')
        amount = int(amount)

        if choice == 'h' or choice == 'health':
            health += amount * health_grow
        elif choice == 'dmg' or choice == 'damage':
            damage += amount * damage_grow
        else:
            defense += amount * defense_grow
        points -= amount
    player = Hero(name, health, damage, defense)
    player.update_inventory()
    print(f'''You created a hero named: {name}. You have these stats:
    health : {player.health}
    damage : {player.damage}
    defense : {player.defense}''')
    return player


def make_a_room(current_room: 'Room' = None):
    number_of_enemies = random.randint(0, 2)
    room_enemies = []
    new_room = Room(prev_room=current_room)
    if current_room:
        current_room.next_room = new_room

    for i in range(number_of_enemies):
        type_of_enemy = random.choice(ALL_ENEMY_TYPES)
        room_enemies.append(type_of_enemy(room=new_room))
    new_room.enemies = room_enemies

    return new_room


def start_a_game():
    player = create_a_hero()
    current_room = make_a_room(current_room=None)
    player.room = current_room
    while player.is_alive():
        action = input(f'''What do you want to do next?
1. Fight enemy(F).
2. Open your inventory(O).
3. Go in another room(G).
''')
        if action == '1' or action == 'F':
            cur_enemies = player.room.enemies
            if len(cur_enemies) > 0:
                for enemy in cur_enemies:
                    print(enemy.name)
                choice = input('Which enemy do you want to fight? ')
                quick_fight = input('Do you want quick battle or normal(with output)?(q for quick) ')
                for enemy in cur_enemies:
                    if enemy.name == choice:
                        winner, loser = player.fight(enemy, quick_fight != 'q')
                        loser.kick_from_room()
                        print(f'{enemy.name} {enemy.get_random_dying_phrase()}')
                        print(f'You won a fight and left with {"%.2f" % player.health}/{player.max_health} health!')
                        break
            else:
                print('There is no enemies in the room!')
        elif action == '2' or action == 'O':
            print(f'''You are wearing:
Weapon: {player.weapon}
Helmet: {player.helmet}
Armor: {player.armor}
Boots: {player.boots}''')
            print('And that is your inventory:')
            inventory_string = ''
            for key, value in player.inventory_for_print.items():
                if isinstance(value, Equipment):
                    inventory_string += f'{value.item_name}'
                else:
                    inventory_string += f'{key} {value}, '
            if len(inventory_string) > 0:
                print(inventory_string)
            else:
                print('\"Nothing here to look at...\"')
        elif action == '3' or action == 'G':
            direction = input('Do you want to go in Previous(P) room or in Next(N) one?')
            while direction != 'P' and direction != 'N':
                print('Your input was incorrect. Try \'P\' or \'N\' next time')
                direction = input('Do you want to go in Previous(P) room or in Next(N) one?')
            if direction == 'P':
                if player.room.prev_room:
                    player.room = player.room.prev_room
                    print('You are going back...')
                else:
                    print('There is no previous room to this room! You started up here!')
            else:
                if player.room.next_room:
                    player.room = player.room.next_room
                else:
                    if player.room.enemies:
                        print('You cannot walk through that room, because you are feeling enemy presence here!')
                    else:
                        player.room = make_a_room(player.room)
                        print('You got into the next room!')


def main():
    start_a_game()


if __name__ == '__main__':
    main()
