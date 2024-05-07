from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class Patient(BaseModel):  
    first_name: str
    last_name: str
    age: int
    dob: str
    address: str
    weight: int
    blood_type : str
    phone: str
    email: str
    gender: str
    room_number: str 
    assign_nurse_id: str = None
    priority: int = None
    note: str = None
    process: bool = False

    def __init__(self, first_name, last_name, age, dob, address, weight, blood_type, phone, email, gender, room_number, assign_nurse_id, priority, note, process=False):
        super().__init__(first_name=first_name, last_name=last_name, age=age, dob=dob, address=address, weight=weight, blood_type=blood_type, phone=phone, email=email, gender=gender, room_number=room_number, assign_nurse_id=assign_nurse_id, priority=priority, note=note, process=process)


    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "age": self.age,
            "dob": self.dob,
            "address": self.address,
            "weight": self.weight,
            "blood_type": self.blood_type,
            "phone": self.phone,
            "email": self.email,
            "gender": self.gender,
            "room_number": self.room_number,
            "assign_nurse_id": self.assign_nurse_id,
            "priority": self.priority,
            "note": self.note,
            "process": self.process
        }

    def __str__(self) -> str:
        return super().__str__()
    
    def __repr__(self) -> str:
        return super().__repr__()
        
@dataclass
class Nurse(BaseModel): 
    first_name: str
    last_name: str
    age: int
    work_shift: str
    phone: str
    email: str = None

    def __init__(self, first_name, last_name, age, work_shift, phone, email):
        super().__init__(first_name=first_name, last_name=last_name, age=age, work_shift=work_shift, phone=phone, email=email)

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "age": self.age,
            "work_shift": self.work_shift,
            "phone": self.phone,
            "email": self.email
        }
    
    def __str__(self) -> str:
        return super().__str__()
    
    def __repr__(self) -> str:
        return super().__repr__()
    