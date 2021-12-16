import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GenreTopArtistsComponent } from './genre-top-artists.component';

describe('GenreTopArtistsComponent', () => {
  let component: GenreTopArtistsComponent;
  let fixture: ComponentFixture<GenreTopArtistsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ GenreTopArtistsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(GenreTopArtistsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
