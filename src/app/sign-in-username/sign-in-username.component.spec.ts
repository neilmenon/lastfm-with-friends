import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SignInUsernameComponent } from './sign-in-username.component';

describe('SignInUsernameComponent', () => {
  let component: SignInUsernameComponent;
  let fixture: ComponentFixture<SignInUsernameComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SignInUsernameComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SignInUsernameComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
