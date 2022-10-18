import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { LayoutModule } from '@angular/cdk/layout';
import { ReactiveFormsModule } from '@angular/forms';

// Angular Material
import { MatSliderModule } from '@angular/material/slider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatMenuModule } from '@angular/material/menu';
import { MatDialogModule } from '@angular/material/dialog';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatMomentDateModule } from '@angular/material-moment-adapter';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatRadioModule } from '@angular/material/radio';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatStepperModule } from '@angular/material/stepper';


// Miscellaneous
import { NgxChartsModule } from '@swimlane/ngx-charts';

// Components & Services
import { AppComponent } from './app.component';
import { HeaderComponent } from './header/header.component';
import { LastfmauthComponent } from './lastfmauth/lastfmauth.component';
import { HomeComponent } from './home/home.component';
import { MessagesComponent } from './messages/messages.component';
import { SignoutComponent } from './signout/signout.component';
import { UserService } from './user.service';
import { CreateGroupComponent } from './create-group/create-group.component';
import { GroupDetailComponent } from './group-detail/group-detail.component';
import { JoinGroupComponent } from './join-group/join-group.component';
import { GroupDashboardComponent } from './group-dashboard/group-dashboard.component';
import { EditGroupComponent } from './edit-group/edit-group.component';
import { ScrobbleHistoryComponent } from './scrobble-history/scrobble-history.component';
import { UserSettingsComponent } from './user-settings/user-settings.component';
import { WhoKnowsTopComponent } from './who-knows-top/who-knows-top.component';
import { CustomDateRangeComponent } from './custom-date-range/custom-date-range.component';
import { ListeningTrendsComponent } from './listening-trends/listening-trends.component';
import { FooterComponent } from './footer/footer.component';
import { PluralizePipe } from './pluralize.pipe';
import { NgRedux, NgReduxModule } from '@angular-redux2/store';
import { INITIAL_STATE, rootReducer } from './store';
import { ConfirmPopupComponent } from './confirm-popup/confirm-popup.component';
import { GroupSessionComponent } from './group-session/group-session.component';
import { TimeSelectionComponent } from './time-selection/time-selection.component';
import { SwitchUserComponent } from './switch-user/switch-user.component';
import { ShortNumberPipe } from './short-number.pipe';
import { GenreTopArtistsComponent } from './genre-top-artists/genre-top-artists.component';
import { SignedInResolverService } from './signed-in-resolver.service';
import { GettingStartedComponent } from './getting-started/getting-started.component';
import { FaqsComponent } from './faqs/faqs.component';
import { PersonalStatsComponent } from './personal-stats/personal-stats.component';
import { AbsolutePipe } from './absolute.pipe';
import { AboutGroupSessionsComponent } from './about-group-sessions/about-group-sessions.component';
import { CreditsComponent } from './credits/credits.component';
import { SignInUsernameComponent } from './sign-in-username/sign-in-username.component';
import { ObservableStore } from './observable-store';
import { createStore } from 'redux';

@NgModule({
  declarations: [
    AppComponent,
    HeaderComponent,
    LastfmauthComponent,
    HomeComponent,
    MessagesComponent,
    SignoutComponent,
    CreateGroupComponent,
    GroupDetailComponent,
    JoinGroupComponent,
    GroupDashboardComponent,
    EditGroupComponent,
    ScrobbleHistoryComponent,
    UserSettingsComponent,
    WhoKnowsTopComponent,
    CustomDateRangeComponent,
    ListeningTrendsComponent,
    FooterComponent,
    PluralizePipe,
    ConfirmPopupComponent,
    GroupSessionComponent,
    TimeSelectionComponent,
    SwitchUserComponent,
    ShortNumberPipe,
    GenreTopArtistsComponent,
    GettingStartedComponent,
    FaqsComponent,
    PersonalStatsComponent,
    AbsolutePipe,
    AboutGroupSessionsComponent,
    CreditsComponent,
    SignInUsernameComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    MatSliderModule,
    LayoutModule,
    MatToolbarModule,
    MatButtonModule,
    MatSidenavModule,
    MatIconModule,
    MatListModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    MatMenuModule,
    MatDialogModule,
    MatTooltipModule,
    MatFormFieldModule,
    HttpClientModule,
    MatInputModule,
    ReactiveFormsModule,
    MatExpansionModule,
    MatProgressBarModule,
    MatSelectModule,
    MatPaginatorModule,
    FormsModule,
    MatDatepickerModule,
    MatMomentDateModule,
    MatAutocompleteModule,
    MatSlideToggleModule,
    NgxChartsModule,
    MatRadioModule,
    NgReduxModule,
    MatCheckboxModule,
    MatChipsModule,
    MatStepperModule,
    RouterModule.forRoot([
      { path: '', component: HomeComponent },
      { path: 'lastfmauth', component: LastfmauthComponent },
      { path: 'signout', component: SignoutComponent, resolve: { result: SignedInResolverService } },
      { path: 'groups/create', component: CreateGroupComponent, resolve: { result: SignedInResolverService } },
      { path: 'groups/join', component: JoinGroupComponent, resolve: { result: SignedInResolverService } },
      { path: 'groups/:joinCode', component: GroupDetailComponent, resolve: { result: SignedInResolverService } },
      { path: 'groups/:joinCode/edit', component: EditGroupComponent, resolve: { result: SignedInResolverService } },
      { path: 'settings', component: UserSettingsComponent, resolve: { result: SignedInResolverService } },
      { path: '**', redirectTo: '' }
    ])
  ],
  providers: [
    UserService,
    PluralizePipe,
    ShortNumberPipe
  ],
  bootstrap: [AppComponent]
})
export class AppModule {
  constructor(ngRedux: ObservableStore<{}>) {
    ngRedux.provideStore(createStore(rootReducer, INITIAL_STATE))
  }
}
