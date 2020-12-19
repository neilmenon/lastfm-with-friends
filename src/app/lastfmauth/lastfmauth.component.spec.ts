import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LastfmauthComponent } from './lastfmauth.component';

describe('LastfmauthComponent', () => {
  let component: LastfmauthComponent;
  let fixture: ComponentFixture<LastfmauthComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ LastfmauthComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LastfmauthComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
