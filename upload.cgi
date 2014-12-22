#! /usr/bin/perl

use strict;
use warnings;
use Template;
use File::Copy;
require './config.pl';


our $FILES_ROOT = "";

my $query = CGI->new();
my $dbh = dbh_connect();

my $username = $query->param("username");
my $description = $query->param("description");
 
my $id = $query->param("id");


my $directory = $query->param("directory");
if ($directory =~ /(\.\.)+/) {
	browser_message("No hax0rs allowed!!!");
}

my $old_directory = $directory;
my $path = "";
if ($directory eq "users/$username") {
	$path = $directory; # HACK!
} elsif ($directory eq "$username/$username") {
	$path = "users/$username";
} else { 
	$path ="users/$directory";
}
if ($directory eq "" || $directory eq $username) {
	$path = "users/$username";
}
if (! -e $path) {
mkdir($path);
}

my $thumbnail = "";
my @files = $query->param("upload");
my %names = $query->param("upload");
my $filename = ""; 


my $fh = "";
foreach my $f (@files) {
	$fh = $f->handle;
	$filename = $f;	

if ($filename eq "") {
	browser_message("St0p trYing t0 H4ck m3!");
	exit;
}

if ($filename !~ /.+[\.jpg|\.JPG]\z/ && $filename !~ /.+[\.png|\.PNG]\z/) {
	browser_message("You can only upload .png and .jpg $filename files.");
	exit 0;
}
my $SQL = "SELECT name FROM files WHERE id = ? AND name = ? AND directory = ?";
my $sth = $dbh->prepare($SQL);
$sth->execute($id, $filename, $directory);
my $exists = $sth->fetchrow();
if ($exists ne "") {
	browser_message("File already exists.", $username, $directory);
	exit 0;
}

my $file = $query->upload("upload");
if (! -e $path && $path ne "") {
	mkdir($path);
	chmod($path, 0764);
}
my $data =""; 
while (my $line = $fh->getline()) {
	$data .= $line;
}
our $DISK_USAGE = 1024 * 1024 * 250; # 250MB!!!

my $disk_use = disk_usage_bytes($username);
my $file_size = length($data);
if (($file_size + $disk_use) > $DISK_USAGE) {
	browser_message("You have used up all your disk space, try removing some files first and then try again.", $username, $directory);
	exit 0;
}
open(FH, ">$path/$filename");
print FH $data;
close FH;
$filename = "$path/$filename";
my $original = $filename;
use Image::Resize;
my $image = Image::Resize->new($filename);
my $gd = $image->resize(240, 160);

$thumbnail = "$filename-small.jpg";
open(FH, ">$thumbnail");
print FH $gd->jpeg();
close FH;

my $number = $query->param("number");
if ($number eq "") {
	$number = 0;
}
$SQL = "INSERT INTO files (name, path, id, directory, description, thumbnail, number) VALUES (?, ?, ?, ?, ?, ?, ?)";
$sth = $dbh->prepare($SQL);
$sth->execute($original, $path, $id, $directory, $description, $thumbnail, $number); 


$dbh->disconnect();


my $cgi = CGI->new();
}

my @pictures = ();
my $i = 0;

my $SQL = "SELECT * FROM files WHERE path = ? ORDER BY -number"; 
my $sth = $dbh->prepare($SQL);
$sth->execute($path); # path or directory?
while(defined(my $file = $sth->fetchrow_hashref())) {
	if ($file->{'name'} !~ /\Aindex.html\z/) {
		$pictures[$i++] = $file;
	}
}

$SQL = "SELECT userid FROM users WHERE username = ?";
$sth = $dbh->prepare($SQL);
$sth->execute($username);
$id = $sth->fetchrow();

$SQL = "SELECT email FROM projects WHERE id = ?";
$sth = $dbh->prepare($SQL);
$sth->execute($id);
my $email = $sth->fetchrow();

use Template;
my $pictures_template = "templates/pictures";

my $vars = {
	USERNAME => $username,
	EMAIL => $email,
	PICTURES => \@pictures,
};

my $template = Template->new();

my $html = "";

$template->process($pictures_template, $vars, \$html) or die "$!\n\n";


my $file = "$path/index.html";

open(FH, ">$file");
print FH $html;
close FH;


my $cgi = CGI->new();
print $cgi->redirect( -location => "/myPortfolio/portal.cgi");
